"""
Operational Intelligence analytics endpoints.

Phase 1: Demand Forecasting — top SKUs, demand projections
Phase 2: Manufacturing Planning Assist — suggestion engine
Phase 3: Delivery Operations — grouping, delayed, priority
Phase 4: Alerting System — stuck orders, negative inventory, backlog
Phase 5: Business Analytics — trends, efficiency, turnover
"""
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, or_, cast, Date

from app.core.database import get_db
from app.core.deps import AdminUser
from app.schemas.common import DataResponse
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.manufacturing_day import ManufacturingDay, ManufacturingDayItem
from app.models.inventory import InventoryItem
from app.models.client import Client
from app.models.sku import SKU

router = APIRouter()


# ══════════════════════════════════════════════════════════════
# PHASE 1: DEMAND FORECASTING
# ══════════════════════════════════════════════════════════════

@router.get("/demand/top-skus")
def get_top_skus(
    current_user: AdminUser,
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365, description="Look-back window in days"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Top-selling SKUs by quantity ordered within the look-back window.
    Only counts orders that were not cancelled.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    results = (
        db.query(
            OrderItem.sku_id,
            SKU.code.label("sku_code"),
            SKU.size,
            SKU.color,
            func.sum(OrderItem.quantity_ordered).label("total_ordered"),
            func.count(func.distinct(OrderItem.order_id)).label("order_count"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .join(SKU, OrderItem.sku_id == SKU.id)
        .filter(
            Order.created_at >= cutoff,
            Order.status != OrderStatus.CANCELLED,
        )
        .group_by(OrderItem.sku_id, SKU.code, SKU.size, SKU.color)
        .order_by(func.sum(OrderItem.quantity_ordered).desc())
        .limit(limit)
        .all()
    )

    data = []
    for row in results:
        # Get current inventory for this SKU
        inv = db.query(InventoryItem).filter(InventoryItem.sku_id == row.sku_id).first()
        product = db.query(SKU).filter(SKU.id == row.sku_id).first()
        product_name = product.product.name if product and product.product else "Unknown"

        data.append({
            "sku_id": str(row.sku_id),
            "sku_code": row.sku_code,
            "product_name": product_name,
            "size": row.size,
            "color": row.color,
            "total_ordered": row.total_ordered,
            "order_count": row.order_count,
            "current_stock": inv.quantity_on_hand if inv else 0,
        })

    return DataResponse(data=data)


@router.get("/demand/forecast")
def get_demand_forecast(
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Demand forecast: projects next 7 and 30 day demand per SKU
    based on historical daily order rates.
    Also shows current outstanding (unallocated) demand.
    """
    now = datetime.now(timezone.utc)
    cutoff_30 = now - timedelta(days=30)
    cutoff_7 = now - timedelta(days=7)

    # 30-day daily rate per SKU
    rates_30 = (
        db.query(
            OrderItem.sku_id,
            func.sum(OrderItem.quantity_ordered).label("total_30d"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            Order.created_at >= cutoff_30,
            Order.status != OrderStatus.CANCELLED,
        )
        .group_by(OrderItem.sku_id)
        .all()
    )
    rate_map_30 = {str(r.sku_id): r.total_30d for r in rates_30}

    # 7-day daily rate per SKU
    rates_7 = (
        db.query(
            OrderItem.sku_id,
            func.sum(OrderItem.quantity_ordered).label("total_7d"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            Order.created_at >= cutoff_7,
            Order.status != OrderStatus.CANCELLED,
        )
        .group_by(OrderItem.sku_id)
        .all()
    )
    rate_map_7 = {str(r.sku_id): r.total_7d for r in rates_7}

    # Current outstanding demand (approved, unallocated)
    outstanding = (
        db.query(
            OrderItem.sku_id,
            func.sum(OrderItem.quantity_ordered - OrderItem.quantity_allocated).label("unallocated"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            Order.status == OrderStatus.APPROVED,
            OrderItem.quantity_allocated < OrderItem.quantity_ordered,
        )
        .group_by(OrderItem.sku_id)
        .all()
    )
    outstanding_map = {str(r.sku_id): r.unallocated for r in outstanding}

    # Build combined set of all SKU IDs
    all_sku_ids = set(rate_map_30.keys()) | set(rate_map_7.keys()) | set(outstanding_map.keys())

    # Fetch SKU details and inventory in bulk
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    sku_objects = db.query(SKU).filter(SKU.id.in_([sid for sid in all_sku_ids])).all() if all_sku_ids else []
    sku_lookup = {str(s.id): s for s in sku_objects}

    inv_objects = db.query(InventoryItem).filter(InventoryItem.sku_id.in_([sid for sid in all_sku_ids])).all() if all_sku_ids else []
    inv_lookup = {str(i.sku_id): i.quantity_on_hand for i in inv_objects}

    data = []
    for sid in all_sku_ids:
        sku = sku_lookup.get(sid)
        if not sku:
            continue

        total_30d = rate_map_30.get(sid, 0)
        total_7d = rate_map_7.get(sid, 0)
        daily_rate_30 = total_30d / 30 if total_30d else 0
        daily_rate_7 = total_7d / 7 if total_7d else 0

        stock = inv_lookup.get(sid, 0)
        outs = outstanding_map.get(sid, 0)

        data.append({
            "sku_id": sid,
            "sku_code": sku.code,
            "product_name": sku.product.name if sku.product else "Unknown",
            "size": sku.size,
            "color": sku.color,
            "current_stock": stock,
            "outstanding_demand": outs,
            "total_ordered_7d": total_7d,
            "total_ordered_30d": total_30d,
            "daily_rate_7d": round(daily_rate_7, 2),
            "daily_rate_30d": round(daily_rate_30, 2),
            "projected_7d": round(daily_rate_7 * 7),
            "projected_30d": round(daily_rate_30 * 30),
            "days_of_stock": round(stock / daily_rate_7, 1) if daily_rate_7 > 0 else None,
        })

    # Sort by highest 7-day demand
    data.sort(key=lambda x: x["total_ordered_7d"], reverse=True)

    return DataResponse(data=data)


# ══════════════════════════════════════════════════════════════
# PHASE 2: MANUFACTURING PLANNING ASSIST
# ══════════════════════════════════════════════════════════════

@router.get("/manufacturing/suggestions")
def get_manufacturing_suggestions(
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Manufacturing suggestion engine: recommends what to manufacture today.
    Considers:
    - Outstanding demand (approved orders with unallocated items)
    - Recent order velocity (7-day trend)
    - Current inventory levels
    - What's already planned for today
    """
    now = datetime.now(timezone.utc)
    today = date.today()
    cutoff_7 = now - timedelta(days=7)

    # 1. Outstanding demand by SKU (approved, unallocated)
    outstanding = (
        db.query(
            OrderItem.sku_id,
            func.sum(OrderItem.quantity_ordered - OrderItem.quantity_allocated).label("unallocated"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            Order.status == OrderStatus.APPROVED,
            OrderItem.quantity_allocated < OrderItem.quantity_ordered,
        )
        .group_by(OrderItem.sku_id)
        .all()
    )
    outstanding_map = {str(r.sku_id): r.unallocated for r in outstanding}

    # 2. 7-day order velocity by SKU
    velocity = (
        db.query(
            OrderItem.sku_id,
            func.sum(OrderItem.quantity_ordered).label("total_7d"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            Order.created_at >= cutoff_7,
            Order.status != OrderStatus.CANCELLED,
        )
        .group_by(OrderItem.sku_id)
        .all()
    )
    velocity_map = {str(r.sku_id): r.total_7d for r in velocity}

    # 3. Current inventory
    inventory = db.query(InventoryItem).all()
    inv_map = {str(i.sku_id): i.quantity_on_hand for i in inventory}

    # 4. Today's plan (what's already planned)
    today_plan = db.query(ManufacturingDay).filter(ManufacturingDay.plan_date == today).first()
    planned_today = {}
    if today_plan:
        for item in today_plan.items:
            planned_today[str(item.sku_id)] = {
                "planned": item.quantity_planned,
                "completed": item.quantity_completed,
            }

    # Combine all SKU IDs
    all_sku_ids = set(outstanding_map.keys()) | set(velocity_map.keys())

    # Fetch SKU details
    sku_objects = db.query(SKU).filter(SKU.id.in_(list(all_sku_ids))).all() if all_sku_ids else []
    sku_lookup = {str(s.id): s for s in sku_objects}

    suggestions = []
    for sid in all_sku_ids:
        sku = sku_lookup.get(sid)
        if not sku or not sku.is_active:
            continue

        demand = outstanding_map.get(sid, 0)
        vel = velocity_map.get(sid, 0)
        stock = inv_map.get(sid, 0)
        daily_rate = vel / 7 if vel else 0

        # Calculate suggested quantity:
        # Start with outstanding demand minus what's in stock
        gap = max(0, demand - stock)

        # Add a buffer based on velocity (1 day's worth)
        buffer = round(daily_rate)
        suggested = gap + buffer

        if suggested <= 0:
            continue

        # Priority scoring: higher = more urgent
        # Weight: outstanding demand * 3 + velocity * 2 - stock
        priority_score = (demand * 3) + (vel * 2) - stock

        plan_info = planned_today.get(sid, None)

        suggestions.append({
            "sku_id": sid,
            "sku_code": sku.code,
            "product_name": sku.product.name if sku.product else "Unknown",
            "size": sku.size,
            "color": sku.color,
            "outstanding_demand": demand,
            "current_stock": stock,
            "velocity_7d": vel,
            "daily_rate": round(daily_rate, 1),
            "suggested_quantity": suggested,
            "priority_score": priority_score,
            "priority": "high" if priority_score > 50 else "medium" if priority_score > 20 else "low",
            "already_planned_today": plan_info["planned"] if plan_info else 0,
            "already_completed_today": plan_info["completed"] if plan_info else 0,
        })

    # Sort by priority score descending
    suggestions.sort(key=lambda x: x["priority_score"], reverse=True)

    return DataResponse(data={
        "suggestions": suggestions,
        "has_plan_today": today_plan is not None,
        "total_suggested_units": sum(s["suggested_quantity"] for s in suggestions),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })


# ══════════════════════════════════════════════════════════════
# PHASE 3: DELIVERY OPERATIONS
# ══════════════════════════════════════════════════════════════

@router.get("/delivery/operations")
def get_delivery_operations(
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Delivery intelligence: groups deliveries by location, highlights
    delayed and high-priority deliveries.
    """
    today = date.today()

    # All orders with delivery assigned (non-terminal)
    active_orders = (
        db.query(Order)
        .filter(
            Order.delivery_team_id.isnot(None),
            Order.status.in_([
                OrderStatus.APPROVED,
                OrderStatus.IN_PRODUCTION,
                OrderStatus.READY_FOR_DELIVERY,
                OrderStatus.OUT_FOR_DELIVERY,
                OrderStatus.PARTIALLY_DELIVERED,
            ]),
        )
        .all()
    )

    # Group by client address (location grouping)
    location_groups = {}
    delayed_orders = []
    priority_orders = []

    for order in active_orders:
        # Determine address
        address = "Unknown Location"
        if order.client and order.client.address:
            address = order.client.address
        elif order.client:
            address = f"Client: {order.client.name}"

        is_delayed = order.delivery_date and order.delivery_date < today
        is_high_priority = (
            is_delayed
            or (order.delivery_date and order.delivery_date == today)
            or order.total_price_rands > 5000  # High-value orders
        )

        order_data = {
            "order_id": str(order.id),
            "client_name": order.client.name if order.client else "Unknown",
            "address": address,
            "delivery_date": order.delivery_date.isoformat() if order.delivery_date else None,
            "status": order.status,
            "delivery_status": order.delivery_status,
            "total_price_rands": float(order.total_price_rands) if order.total_price_rands else 0,
            "delivery_team_id": str(order.delivery_team_id) if order.delivery_team_id else None,
            "delivery_team_name": order.delivery_team.name if order.delivery_team else None,
            "is_delayed": is_delayed,
            "is_high_priority": is_high_priority,
            "days_overdue": (today - order.delivery_date).days if is_delayed else 0,
            "item_count": len(order.items),
        }

        # Group by location
        if address not in location_groups:
            location_groups[address] = {
                "address": address,
                "orders": [],
                "total_value": 0,
                "has_delayed": False,
            }
        location_groups[address]["orders"].append(order_data)
        location_groups[address]["total_value"] += order_data["total_price_rands"]
        if is_delayed:
            location_groups[address]["has_delayed"] = True
            delayed_orders.append(order_data)
        if is_high_priority:
            priority_orders.append(order_data)

    # Convert to sorted list
    location_list = sorted(
        location_groups.values(),
        key=lambda g: (not g["has_delayed"], -g["total_value"]),
    )

    # Add order counts to each group
    for group in location_list:
        group["order_count"] = len(group["orders"])

    return DataResponse(data={
        "locations": location_list,
        "delayed_orders": sorted(delayed_orders, key=lambda o: o["days_overdue"], reverse=True),
        "priority_orders": sorted(priority_orders, key=lambda o: -o["total_price_rands"]),
        "summary": {
            "total_active_deliveries": len(active_orders),
            "total_locations": len(location_list),
            "delayed_count": len(delayed_orders),
            "priority_count": len(priority_orders),
            "today_count": sum(1 for o in active_orders if o.delivery_date == today),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })


# ══════════════════════════════════════════════════════════════
# PHASE 4: ALERTING SYSTEM
# ══════════════════════════════════════════════════════════════

@router.get("/alerts")
def get_system_alerts(
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    System alerts: identifies conditions requiring attention.
    - Orders stuck in approved >48 hours
    - Negative inventory
    - Manufacturing backlog above threshold
    - Delayed deliveries
    """
    now = datetime.now(timezone.utc)
    today = date.today()
    alerts = []

    # ── 1. Stuck Orders: Approved > 48 hours without progress ──
    cutoff_48h = now - timedelta(hours=48)
    stuck_orders = (
        db.query(Order)
        .filter(
            Order.status == OrderStatus.APPROVED,
            Order.created_at < cutoff_48h,
        )
        .all()
    )
    for order in stuck_orders:
        hours_stuck = int((now - order.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600)
        alerts.append({
            "type": "stuck_order",
            "severity": "high" if hours_stuck > 96 else "medium",
            "title": f"Order stuck in Approved for {hours_stuck}h",
            "description": f"Order for {order.client.name if order.client else 'Unknown'} — R{order.total_price_rands:,.2f}" if order.total_price_rands else f"Order stuck for {hours_stuck}h",
            "entity_type": "order",
            "entity_id": str(order.id),
            "metric": hours_stuck,
            "created_at": order.created_at.isoformat() if order.created_at else None,
        })

    # ── 2. Negative Inventory ──
    negative_inventory = (
        db.query(InventoryItem)
        .filter(InventoryItem.quantity_on_hand < 0)
        .all()
    )
    for item in negative_inventory:
        sku_code = item.sku.code if item.sku else "Unknown"
        alerts.append({
            "type": "negative_inventory",
            "severity": "high",
            "title": f"Negative inventory: {sku_code}",
            "description": f"{sku_code} has {item.quantity_on_hand} units on hand",
            "entity_type": "inventory",
            "entity_id": str(item.id),
            "metric": item.quantity_on_hand,
        })

    # ── 3. Manufacturing Backlog ──
    # Outstanding demand where unallocated > 100 units for a single SKU
    backlog_items = (
        db.query(
            OrderItem.sku_id,
            SKU.code.label("sku_code"),
            func.sum(OrderItem.quantity_ordered - OrderItem.quantity_allocated).label("unallocated"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .join(SKU, OrderItem.sku_id == SKU.id)
        .filter(
            Order.status == OrderStatus.APPROVED,
            OrderItem.quantity_allocated < OrderItem.quantity_ordered,
        )
        .group_by(OrderItem.sku_id, SKU.code)
        .having(func.sum(OrderItem.quantity_ordered - OrderItem.quantity_allocated) > 50)
        .all()
    )
    for item in backlog_items:
        alerts.append({
            "type": "manufacturing_backlog",
            "severity": "high" if item.unallocated > 200 else "medium",
            "title": f"Manufacturing backlog: {item.sku_code}",
            "description": f"{item.unallocated} units unallocated for {item.sku_code}",
            "entity_type": "sku",
            "entity_id": str(item.sku_id),
            "metric": item.unallocated,
        })

    # ── 4. Delayed Deliveries ──
    delayed = (
        db.query(Order)
        .filter(
            Order.delivery_date < today,
            Order.status.in_([
                OrderStatus.APPROVED,
                OrderStatus.IN_PRODUCTION,
                OrderStatus.READY_FOR_DELIVERY,
                OrderStatus.OUT_FOR_DELIVERY,
                OrderStatus.PARTIALLY_DELIVERED,
            ]),
        )
        .all()
    )
    for order in delayed:
        days_overdue = (today - order.delivery_date).days
        alerts.append({
            "type": "delayed_delivery",
            "severity": "high" if days_overdue > 7 else "medium" if days_overdue > 3 else "low",
            "title": f"Delivery overdue by {days_overdue} day{'s' if days_overdue != 1 else ''}",
            "description": f"Order for {order.client.name if order.client else 'Unknown'} — due {order.delivery_date.isoformat()}",
            "entity_type": "order",
            "entity_id": str(order.id),
            "metric": days_overdue,
        })

    # ── 5. Low Stock Alert ──
    # SKUs with recent demand but < 3 days of stock remaining
    cutoff_7 = now - timedelta(days=7)
    recent_demand = (
        db.query(
            OrderItem.sku_id,
            func.sum(OrderItem.quantity_ordered).label("demand_7d"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            Order.created_at >= cutoff_7,
            Order.status != OrderStatus.CANCELLED,
        )
        .group_by(OrderItem.sku_id)
        .all()
    )

    for row in recent_demand:
        daily_rate = row.demand_7d / 7
        if daily_rate < 1:
            continue
        inv = db.query(InventoryItem).filter(InventoryItem.sku_id == row.sku_id).first()
        stock = inv.quantity_on_hand if inv else 0
        if stock <= 0:
            continue  # Already covered by negative inventory or zero stock
        days_remaining = stock / daily_rate
        if days_remaining < 3:
            sku = db.query(SKU).filter(SKU.id == row.sku_id).first()
            sku_code = sku.code if sku else "Unknown"
            alerts.append({
                "type": "low_stock",
                "severity": "medium" if days_remaining > 1 else "high",
                "title": f"Low stock: {sku_code}",
                "description": f"{stock} units remaining (~{days_remaining:.1f} days at current demand)",
                "entity_type": "inventory",
                "entity_id": str(inv.id) if inv else None,
                "metric": round(days_remaining, 1),
            })

    # Sort by severity (high first) then type
    severity_order = {"high": 0, "medium": 1, "low": 2}
    alerts.sort(key=lambda a: (severity_order.get(a["severity"], 3), a["type"]))

    return DataResponse(data={
        "alerts": alerts,
        "summary": {
            "total": len(alerts),
            "high": sum(1 for a in alerts if a["severity"] == "high"),
            "medium": sum(1 for a in alerts if a["severity"] == "medium"),
            "low": sum(1 for a in alerts if a["severity"] == "low"),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })


# ══════════════════════════════════════════════════════════════
# PHASE 5: BUSINESS ANALYTICS
# ══════════════════════════════════════════════════════════════

@router.get("/business/overview")
def get_business_overview(
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Business analytics overview:
    - Sales trends (7d, 30d, 90d)
    - Manufacturing efficiency
    - Delivery completion rate
    - Inventory turnover
    """
    now = datetime.now(timezone.utc)
    today = date.today()

    # ── Sales Trends ──────────────────────────────────────────
    def sales_for_period(days: int):
        cutoff = now - timedelta(days=days)
        result = (
            db.query(
                func.count(Order.id).label("order_count"),
                func.sum(Order.total_price_rands).label("revenue"),
                func.sum(
                    case(
                        (Order.status == OrderStatus.CANCELLED, 1),
                        else_=0,
                    )
                ).label("cancelled_count"),
            )
            .filter(Order.created_at >= cutoff)
            .first()
        )
        return {
            "order_count": result.order_count or 0,
            "revenue": float(result.revenue or 0),
            "cancelled_count": result.cancelled_count or 0,
        }

    sales_7d = sales_for_period(7)
    sales_30d = sales_for_period(30)
    sales_90d = sales_for_period(90)

    # Average order value
    avg_order_value_30d = sales_30d["revenue"] / sales_30d["order_count"] if sales_30d["order_count"] > 0 else 0

    # ── Sales by Day (last 14 days for sparkline) ─────────────
    cutoff_14 = now - timedelta(days=14)
    daily_sales = (
        db.query(
            cast(Order.created_at, Date).label("day"),
            func.count(Order.id).label("orders"),
            func.sum(Order.total_price_rands).label("revenue"),
        )
        .filter(
            Order.created_at >= cutoff_14,
            Order.status != OrderStatus.CANCELLED,
        )
        .group_by(cast(Order.created_at, Date))
        .order_by(cast(Order.created_at, Date))
        .all()
    )

    sales_trend = []
    for row in daily_sales:
        sales_trend.append({
            "date": row.day.isoformat() if row.day else None,
            "orders": row.orders,
            "revenue": float(row.revenue or 0),
        })

    # ── Manufacturing Efficiency ──────────────────────────────
    # Last 30 days of plans
    cutoff_30_date = today - timedelta(days=30)
    mfg_plans = (
        db.query(ManufacturingDay)
        .filter(ManufacturingDay.plan_date >= cutoff_30_date)
        .all()
    )

    total_planned = 0
    total_completed = 0
    plan_count = len(mfg_plans)
    for plan in mfg_plans:
        for item in plan.items:
            total_planned += item.quantity_planned
            total_completed += item.quantity_completed

    mfg_efficiency = round((total_completed / total_planned * 100), 1) if total_planned > 0 else 0

    # ── Delivery Completion Rate ──────────────────────────────
    # Last 30 days
    cutoff_30 = now - timedelta(days=30)
    delivery_stats = (
        db.query(
            func.count(Order.id).label("total"),
            func.sum(
                case(
                    (Order.status == OrderStatus.COMPLETED, 1),
                    else_=0,
                )
            ).label("completed"),
            func.sum(
                case(
                    (Order.status == OrderStatus.PARTIALLY_DELIVERED, 1),
                    else_=0,
                )
            ).label("partial"),
        )
        .filter(
            Order.delivery_date >= cutoff_30_date,
            Order.delivery_team_id.isnot(None),
        )
        .first()
    )

    total_deliveries = delivery_stats.total or 0
    completed_deliveries = delivery_stats.completed or 0
    partial_deliveries = delivery_stats.partial or 0
    delivery_completion_rate = round((completed_deliveries / total_deliveries * 100), 1) if total_deliveries > 0 else 0

    # On-time delivery rate
    on_time_count = (
        db.query(func.count(Order.id))
        .filter(
            Order.status == OrderStatus.COMPLETED,
            Order.delivered_at.isnot(None),
            Order.delivery_date >= cutoff_30_date,
            cast(Order.delivered_at, Date) <= Order.delivery_date,
        )
        .scalar()
    ) or 0
    on_time_rate = round((on_time_count / completed_deliveries * 100), 1) if completed_deliveries > 0 else 0

    # ── Inventory Turnover ────────────────────────────────────
    # Units sold (delivered) in last 30 days vs avg inventory
    units_delivered_30d = (
        db.query(func.sum(OrderItem.quantity_delivered))
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            Order.status.in_([OrderStatus.COMPLETED, OrderStatus.PARTIALLY_DELIVERED]),
            Order.delivered_at >= cutoff_30,
        )
        .scalar()
    ) or 0

    total_inventory = (
        db.query(func.sum(InventoryItem.quantity_on_hand)).scalar()
    ) or 0

    # Annualized turnover: (monthly deliveries * 12) / current inventory
    inventory_turnover = round(((units_delivered_30d * 12) / total_inventory), 2) if total_inventory > 0 else 0

    # ── Top Clients (by revenue, last 30 days) ────────────────
    top_clients = (
        db.query(
            Client.name,
            func.count(Order.id).label("order_count"),
            func.sum(Order.total_price_rands).label("revenue"),
        )
        .join(Order, Client.id == Order.client_id)
        .filter(
            Order.created_at >= cutoff_30,
            Order.status != OrderStatus.CANCELLED,
        )
        .group_by(Client.name)
        .order_by(func.sum(Order.total_price_rands).desc())
        .limit(5)
        .all()
    )

    return DataResponse(data={
        "sales": {
            "last_7d": sales_7d,
            "last_30d": sales_30d,
            "last_90d": sales_90d,
            "avg_order_value_30d": round(avg_order_value_30d, 2),
            "trend": sales_trend,
        },
        "manufacturing": {
            "efficiency_30d": mfg_efficiency,
            "total_planned_30d": total_planned,
            "total_completed_30d": total_completed,
            "plan_count_30d": plan_count,
        },
        "delivery": {
            "completion_rate_30d": delivery_completion_rate,
            "on_time_rate_30d": on_time_rate,
            "total_deliveries_30d": total_deliveries,
            "completed_30d": completed_deliveries,
            "partial_30d": partial_deliveries,
        },
        "inventory": {
            "total_on_hand": total_inventory,
            "units_delivered_30d": units_delivered_30d,
            "turnover_annualized": inventory_turnover,
        },
        "top_clients": [
            {
                "name": c.name,
                "order_count": c.order_count,
                "revenue": float(c.revenue or 0),
            }
            for c in top_clients
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })
