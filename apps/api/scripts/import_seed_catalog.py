"""
Import store, sales agent, delivery teams, and products payload.
Idempotent: safe to re-run.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.store import Store
from app.models.sales_agent import SalesAgent
from app.models.delivery_team import DeliveryTeam
from app.models.delivery_team_member import DeliveryTeamMember
from app.services.store import StoreService
from app.services.sales_agent import SalesAgentService
from app.services.delivery_team import DeliveryTeamService
from app.services.product import ProductService
from app.schemas.store import StoreCreate, StoreUpdate
from app.schemas.sales_agent import SalesAgentCreate, SalesAgentUpdate
from app.schemas.delivery_team import DeliveryTeamCreate, DeliveryTeamMemberCreate, DeliveryTeamUpdate
from app.schemas.product import ProductBulkImportRequest


PRODUCTS_TO_IMPORT = {
  "products": [
    {
      "name": "Premium Bolivia Trough Plant Pot",
      "category": "Concrete Pots",
      "description_html": "",
      "skus": [
        { "code": "PBOLTRPP-LG-AMP", "size": "Large | 280mm x 325mm x 715mm", "color": "Amper", "base_price_rands": 901.0, "stock_quantity": 0 },
        { "code": "PBOLTRPP-LG-CHR", "size": "Large | 280mm x 325mm x 715mm", "color": "Chryso Black", "base_price_rands": 901.0, "stock_quantity": 0 },
        { "code": "PBOLTRPP-LG-FWH", "size": "Large | 280mm x 325mm x 715mm", "color": "Flinted White", "base_price_rands": 901.0, "stock_quantity": 0 },
        { "code": "PBOLTRPP-LG-GRL", "size": "Large | 280mm x 325mm x 715mm", "color": "Granite light", "base_price_rands": 901.0, "stock_quantity": 0 },
        { "code": "PBOLTRPP-LG-GRD", "size": "Large | 280mm x 325mm x 715mm", "color": "Granite dark", "base_price_rands": 901.0, "stock_quantity": 0 },
        { "code": "PBOLTRPP-LG-ROC", "size": "Large | 280mm x 325mm x 715mm", "color": "Rock", "base_price_rands": 901.0, "stock_quantity": 0 },
        { "code": "PBOLTRPP-LG-VEL", "size": "Large | 280mm x 325mm x 715mm", "color": "Velvet", "base_price_rands": 901.0, "stock_quantity": 0 },
        { "code": "PBOLTRPP-LG-GRA", "size": "Large | 280mm x 325mm x 715mm", "color": "Granite light sealed", "base_price_rands": 901.0, "stock_quantity": 0 },
        { "code": "PBOLTRPP-LG-GRA-2", "size": "Large | 280mm x 325mm x 715mm", "color": "Granite dark sealed", "base_price_rands": 901.0, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Premium Tennessee Concrete pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "PTENCPOT-MD-AMP", "size": "Medium  600mm x 640mm", "color": "Amper", "base_price_rands": 1548.57, "stock_quantity": 0 },
        { "code": "PTENCPOT-MD-FWH", "size": "Medium  600mm x 640mm", "color": "Flinted White", "base_price_rands": 1548.57, "stock_quantity": 0 },
        { "code": "PTENCPOT-MD-GRL", "size": "Medium  600mm x 640mm", "color": "Granite light", "base_price_rands": 1548.57, "stock_quantity": 0 },
        { "code": "PTENCPOT-MD-GRD", "size": "Medium  600mm x 640mm", "color": "Granite dark", "base_price_rands": 1548.57, "stock_quantity": 0 },
        { "code": "PTENCPOT-MD-ROC", "size": "Medium  600mm x 640mm", "color": "Rock", "base_price_rands": 1548.57, "stock_quantity": 0 },
        { "code": "PTENCPOT-MD-VEL", "size": "Medium  600mm x 640mm", "color": "Velvet", "base_price_rands": 1548.57, "stock_quantity": 0 },
        { "code": "PTENCPOT-MD-CHR", "size": "Medium  600mm x 640mm", "color": "Chryso Black", "base_price_rands": 1548.57, "stock_quantity": 0 },
        { "code": "PTENCPOT-MD-GRA", "size": "Medium  600mm x 640mm", "color": "Granite dark sealed", "base_price_rands": 1548.57, "stock_quantity": 0 },
        { "code": "PTENCPOT-MD-GRA-2", "size": "Medium  600mm x 640mm", "color": "Granite light sealed", "base_price_rands": 1548.57, "stock_quantity": 0 },
        { "code": "PTENCPOT-MD-CHA", "size": "Medium  600mm x 640mm", "color": "Charcoal light", "base_price_rands": 1548.57, "stock_quantity": 0 },
        { "code": "PTENCPOT-MD-CHA-2", "size": "Medium  600mm x 640mm", "color": "Charcoal dark", "base_price_rands": 1548.57, "stock_quantity": 0 },
        { "code": "PTENCPOT-LG-AMP", "size": "Large  840mm x 580mm", "color": "Amper", "base_price_rands": 2126.27, "stock_quantity": 0 },
        { "code": "PTENCPOT-LG-FWH", "size": "Large  840mm x 580mm", "color": "Flinted White", "base_price_rands": 2126.27, "stock_quantity": 0 },
        { "code": "PTENCPOT-LG-GRL", "size": "Large  840mm x 580mm", "color": "Granite light", "base_price_rands": 2126.27, "stock_quantity": 0 },
        { "code": "PTENCPOT-LG-GRD", "size": "Large  840mm x 580mm", "color": "Granite dark", "base_price_rands": 2126.27, "stock_quantity": 0 },
        { "code": "PTENCPOT-LG-ROC", "size": "Large  840mm x 580mm", "color": "Rock", "base_price_rands": 2126.27, "stock_quantity": 0 },
        { "code": "PTENCPOT-LG-VEL", "size": "Large  840mm x 580mm", "color": "Velvet", "base_price_rands": 2126.27, "stock_quantity": 0 },
        { "code": "PTENCPOT-LG-CHR", "size": "Large  840mm x 580mm", "color": "Chryso Black", "base_price_rands": 2126.27, "stock_quantity": 0 },
        { "code": "PTENCPOT-LG-GRA", "size": "Large  840mm x 580mm", "color": "Granite dark sealed", "base_price_rands": 2126.27, "stock_quantity": 0 },
        { "code": "PTENCPOT-LG-GRA-2", "size": "Large  840mm x 580mm", "color": "Granite light sealed", "base_price_rands": 2126.27, "stock_quantity": 0 },
        { "code": "PTENCPOT-LG-CHA", "size": "Large  840mm x 580mm", "color": "Charcoal light", "base_price_rands": 2126.27, "stock_quantity": 0 },
        { "code": "PTENCPOT-LG-CHA-2", "size": "Large  840mm x 580mm", "color": "Charcoal dark", "base_price_rands": 2126.27, "stock_quantity": 0 },
        { "code": "PTENCPOT-SM-AMP", "size": "Small 390mm x 405mm", "color": "Amper", "base_price_rands": 732.78, "stock_quantity": 0 },
        { "code": "PTENCPOT-SM-FWH", "size": "Small 390mm x 405mm", "color": "Flinted White", "base_price_rands": 732.78, "stock_quantity": 0 },
        { "code": "PTENCPOT-SM-GRL", "size": "Small 390mm x 405mm", "color": "Granite light", "base_price_rands": 732.78, "stock_quantity": 0 },
        { "code": "PTENCPOT-SM-GRD", "size": "Small 390mm x 405mm", "color": "Granite dark", "base_price_rands": 732.78, "stock_quantity": 0 },
        { "code": "PTENCPOT-SM-ROC", "size": "Small 390mm x 405mm", "color": "Rock", "base_price_rands": 732.78, "stock_quantity": 0 },
        { "code": "PTENCPOT-SM-VEL", "size": "Small 390mm x 405mm", "color": "Velvet", "base_price_rands": 732.78, "stock_quantity": 0 },
        { "code": "PTENCPOT-SM-CHR", "size": "Small 390mm x 405mm", "color": "Chryso Black", "base_price_rands": 732.78, "stock_quantity": 0 },
        { "code": "PTENCPOT-SM-GRA", "size": "Small 390mm x 405mm", "color": "Granite dark sealed", "base_price_rands": 732.78, "stock_quantity": 0 },
        { "code": "PTENCPOT-SM-GRA-2", "size": "Small 390mm x 405mm", "color": "Granite light sealed", "base_price_rands": 732.78, "stock_quantity": 0 },
        { "code": "PTENCPOT-SM-CHA", "size": "Small 390mm x 405mm", "color": "Charcoal light", "base_price_rands": 732.78, "stock_quantity": 0 },
        { "code": "PTENCPOT-SM-CHA-2", "size": "Small 390mm x 405mm", "color": "Charcoal dark", "base_price_rands": 732.78, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Premium Chunky Trough Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "PCHUTRPP-SM-AMP", "size": "Small | 310mm X 300mm X 600mm", "color": "Amper", "base_price_rands": 811.76, "stock_quantity": 0 },
        { "code": "PCHUTRPP-SM-FWH", "size": "Small | 310mm X 300mm X 600mm", "color": "Flinted White", "base_price_rands": 811.76, "stock_quantity": 0 },
        { "code": "PCHUTRPP-SM-GRD", "size": "Small | 310mm X 300mm X 600mm", "color": "Granite dark", "base_price_rands": 811.76, "stock_quantity": 0 },
        { "code": "PCHUTRPP-SM-GRL", "size": "Small | 310mm X 300mm X 600mm", "color": "Granite light", "base_price_rands": 811.76, "stock_quantity": 0 },
        { "code": "PCHUTRPP-SM-ROC", "size": "Small | 310mm X 300mm X 600mm", "color": "Rock", "base_price_rands": 811.76, "stock_quantity": 0 },
        { "code": "PCHUTRPP-SM-VEL", "size": "Small | 310mm X 300mm X 600mm", "color": "Velvet", "base_price_rands": 811.76, "stock_quantity": 0 },
        { "code": "PCHUTRPP-SM-CHR", "size": "Small | 310mm X 300mm X 600mm", "color": "Chryso Black", "base_price_rands": 811.76, "stock_quantity": 0 },
        { "code": "PCHUTRPP-MD-AMP", "size": "Medium | 410mm X 350mm X 750mm", "color": "Amper", "base_price_rands": 1380.0, "stock_quantity": 0 },
        { "code": "PCHUTRPP-MD-FWH", "size": "Medium | 410mm X 350mm X 750mm", "color": "Flinted White", "base_price_rands": 1380.0, "stock_quantity": 0 },
        { "code": "PCHUTRPP-MD-GRD", "size": "Medium | 410mm X 350mm X 750mm", "color": "Granite dark", "base_price_rands": 1380.0, "stock_quantity": 0 },
        { "code": "PCHUTRPP-MD-GRL", "size": "Medium | 410mm X 350mm X 750mm", "color": "Granite light", "base_price_rands": 1380.0, "stock_quantity": 0 },
        { "code": "PCHUTRPP-MD-ROC", "size": "Medium | 410mm X 350mm X 750mm", "color": "Rock", "base_price_rands": 1380.0, "stock_quantity": 0 },
        { "code": "PCHUTRPP-MD-VEL", "size": "Medium | 410mm X 350mm X 750mm", "color": "Velvet", "base_price_rands": 1380.0, "stock_quantity": 0 },
        { "code": "PCHUTRPP-MD-CHR", "size": "Medium | 410mm X 350mm X 750mm", "color": "Chryso Black", "base_price_rands": 1380.0, "stock_quantity": 0 },
        { "code": "PCHUTRPP-LG-AMP", "size": "Large | 460mm X 400mm X 95mm", "color": "Amper", "base_price_rands": 1867.06, "stock_quantity": 0 },
        { "code": "PCHUTRPP-LG-FWH", "size": "Large | 460mm X 400mm X 95mm", "color": "Flinted White", "base_price_rands": 1867.06, "stock_quantity": 0 },
        { "code": "PCHUTRPP-LG-GRD", "size": "Large | 460mm X 400mm X 95mm", "color": "Granite dark", "base_price_rands": 1867.06, "stock_quantity": 0 },
        { "code": "PCHUTRPP-LG-GRL", "size": "Large | 460mm X 400mm X 95mm", "color": "Granite light", "base_price_rands": 1867.06, "stock_quantity": 0 },
        { "code": "PCHUTRPP-LG-ROC", "size": "Large | 460mm X 400mm X 95mm", "color": "Rock", "base_price_rands": 1867.06, "stock_quantity": 0 },
        { "code": "PCHUTRPP-LG-VEL", "size": "Large | 460mm X 400mm X 95mm", "color": "Velvet", "base_price_rands": 1867.06, "stock_quantity": 0 },
        { "code": "PCHUTRPP-LG-CHR", "size": "Large | 460mm X 400mm X 95mm", "color": "Chryso Black", "base_price_rands": 1867.06, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Premium Tulip Plant Pot",
      "category": "Concrete Pots",
      "description_html": "",
      "skus": [
        { "code": "PTULPP-SM-AMP", "size": "Small | 510mm X 360mm", "color": "Amper", "base_price_rands": 918.29, "stock_quantity": 0 },
        { "code": "PTULPP-SM-FWH", "size": "Small | 510mm X 360mm", "color": "Flinted White", "base_price_rands": 918.29, "stock_quantity": 0 },
        { "code": "PTULPP-SM-GRA", "size": "Small | 510mm X 360mm", "color": "Granite", "base_price_rands": 918.29, "stock_quantity": 0 },
        { "code": "PTULPP-SM-GRA-2", "size": "Small | 510mm X 360mm", "color": "Granite Sealed", "base_price_rands": 918.29, "stock_quantity": 0 },
        { "code": "PTULPP-SM-ROC", "size": "Small | 510mm X 360mm", "color": "Rock", "base_price_rands": 918.29, "stock_quantity": 0 },
        { "code": "PTULPP-SM-VEL", "size": "Small | 510mm X 360mm", "color": "Velvet", "base_price_rands": 918.29, "stock_quantity": 0 },
        { "code": "PTULPP-SM-TER", "size": "Small | 510mm X 360mm", "color": "Terracotta", "base_price_rands": 918.29, "stock_quantity": 0 },
        { "code": "PTULPP-SM-CHR", "size": "Small | 510mm X 360mm", "color": "Chryso Black", "base_price_rands": 918.29, "stock_quantity": 0 },
        { "code": "PTULPP-MD-AMP", "size": "Medium | 620mm X 460mm", "color": "Amper", "base_price_rands": 1273.6, "stock_quantity": 0 },
        { "code": "PTULPP-MD-FWH", "size": "Medium | 620mm X 460mm", "color": "Flinted White", "base_price_rands": 1273.6, "stock_quantity": 0 },
        { "code": "PTULPP-MD-GRA", "size": "Medium | 620mm X 460mm", "color": "Granite", "base_price_rands": 1273.6, "stock_quantity": 0 },
        { "code": "PTULPP-MD-GRA-2", "size": "Medium | 620mm X 460mm", "color": "Granite Sealed", "base_price_rands": 1273.6, "stock_quantity": 0 },
        { "code": "PTULPP-MD-ROC", "size": "Medium | 620mm X 460mm", "color": "Rock", "base_price_rands": 1273.6, "stock_quantity": 0 },
        { "code": "PTULPP-MD-VEL", "size": "Medium | 620mm X 460mm", "color": "Velvet", "base_price_rands": 1273.6, "stock_quantity": 0 },
        { "code": "PTULPP-MD-TER", "size": "Medium | 620mm X 460mm", "color": "Terracotta", "base_price_rands": 1273.6, "stock_quantity": 0 },
        { "code": "PTULPP-MD-CHR", "size": "Medium | 620mm X 460mm", "color": "Chryso Black", "base_price_rands": 1273.6, "stock_quantity": 0 },
        { "code": "PTULPP-LG-AMP", "size": "Large | 780mm X 482mm", "color": "Amper", "base_price_rands": 1766.1, "stock_quantity": 0 },
        { "code": "PTULPP-LG-FWH", "size": "Large | 780mm X 482mm", "color": "Flinted White", "base_price_rands": 1766.1, "stock_quantity": 0 },
        { "code": "PTULPP-LG-GRA", "size": "Large | 780mm X 482mm", "color": "Granite", "base_price_rands": 1766.1, "stock_quantity": 0 },
        { "code": "PTULPP-LG-GRA-2", "size": "Large | 780mm X 482mm", "color": "Granite Sealed", "base_price_rands": 1766.1, "stock_quantity": 0 },
        { "code": "PTULPP-LG-ROC", "size": "Large | 780mm X 482mm", "color": "Rock", "base_price_rands": 1766.1, "stock_quantity": 0 },
        { "code": "PTULPP-LG-VEL", "size": "Large | 780mm X 482mm", "color": "Velvet", "base_price_rands": 1766.1, "stock_quantity": 0 },
        { "code": "PTULPP-LG-TER", "size": "Large | 780mm X 482mm", "color": "Terracotta", "base_price_rands": 1766.1, "stock_quantity": 0 },
        { "code": "PTULPP-LG-CHR", "size": "Large | 780mm X 482mm", "color": "Chryso Black", "base_price_rands": 1766.1, "stock_quantity": 0 },
        { "code": "PTULPP-XL-AMP", "size": "Extra Large | 980mm X 420mm", "color": "Amper", "base_price_rands": 2226.0, "stock_quantity": 0 },
        { "code": "PTULPP-XL-FWH", "size": "Extra Large | 980mm X 420mm", "color": "Flinted White", "base_price_rands": 2226.0, "stock_quantity": 0 },
        { "code": "PTULPP-XL-GRA", "size": "Extra Large | 980mm X 420mm", "color": "Granite", "base_price_rands": 2226.0, "stock_quantity": 0 },
        { "code": "PTULPP-XL-GRA-2", "size": "Extra Large | 980mm X 420mm", "color": "Granite Sealed", "base_price_rands": 2226.0, "stock_quantity": 0 },
        { "code": "PTULPP-XL-ROC", "size": "Extra Large | 980mm X 420mm", "color": "Rock", "base_price_rands": 2226.0, "stock_quantity": 0 },
        { "code": "PTULPP-XL-VEL", "size": "Extra Large | 980mm X 420mm", "color": "Velvet", "base_price_rands": 2226.0, "stock_quantity": 0 },
        { "code": "PTULPP-XL-TER", "size": "Extra Large | 980mm X 420mm", "color": "Terracotta", "base_price_rands": 2226.0, "stock_quantity": 0 },
        { "code": "PTULPP-XL-CHR", "size": "Extra Large | 980mm X 420mm", "color": "Chryso Black", "base_price_rands": 2226.0, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Premium Protea Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "PPROPP-SM-AMP", "size": "Small | 730mm x 400mm", "color": "Amper", "base_price_rands": 885.44, "stock_quantity": 0 },
        { "code": "PPROPP-SM-FWH", "size": "Small | 730mm x 400mm", "color": "Flinted White", "base_price_rands": 804.2, "stock_quantity": 0 },
        { "code": "PPROPP-SM-GRA", "size": "Small | 730mm x 400mm", "color": "Granite", "base_price_rands": 804.2, "stock_quantity": 0 },
        { "code": "PPROPP-SM-GRA-2", "size": "Small | 730mm x 400mm", "color": "Granite Sealed", "base_price_rands": 804.2, "stock_quantity": 0 },
        { "code": "PPROPP-SM-ROC", "size": "Small | 730mm x 400mm", "color": "Rock", "base_price_rands": 804.2, "stock_quantity": 0 },
        { "code": "PPROPP-SM-VEL", "size": "Small | 730mm x 400mm", "color": "Velvet", "base_price_rands": 804.2, "stock_quantity": 0 },
        { "code": "PPROPP-SM-CHR", "size": "Small | 730mm x 400mm", "color": "Chryso Black", "base_price_rands": 804.2, "stock_quantity": 0 },
        { "code": "PPROPP-MD-AMP", "size": "Medium | 950mm x 480mm", "color": "Amper", "base_price_rands": 1336.95, "stock_quantity": 0 },
        { "code": "PPROPP-MD-FWH", "size": "Medium | 950mm x 480mm", "color": "Flinted White", "base_price_rands": 1336.95, "stock_quantity": 0 },
        { "code": "PPROPP-MD-GRA", "size": "Medium | 950mm x 480mm", "color": "Granite", "base_price_rands": 1336.95, "stock_quantity": 0 },
        { "code": "PPROPP-MD-GRA-2", "size": "Medium | 950mm x 480mm", "color": "Granite Sealed", "base_price_rands": 1336.95, "stock_quantity": 0 },
        { "code": "PPROPP-MD-ROC", "size": "Medium | 950mm x 480mm", "color": "Rock", "base_price_rands": 1336.95, "stock_quantity": 0 },
        { "code": "PPROPP-MD-VEL", "size": "Medium | 950mm x 480mm", "color": "Velvet", "base_price_rands": 1336.95, "stock_quantity": 0 },
        { "code": "PPROPP-MD-CHR", "size": "Medium | 950mm x 480mm", "color": "Chryso Black", "base_price_rands": 804.2, "stock_quantity": 0 },
        { "code": "PPROPP-LG-AMP", "size": "Large | 1050mm x 500mm", "color": "Amper", "base_price_rands": 1819.45, "stock_quantity": 0 },
        { "code": "PPROPP-LG-FWH", "size": "Large | 1050mm x 500mm", "color": "Flinted White", "base_price_rands": 1819.45, "stock_quantity": 0 },
        { "code": "PPROPP-LG-GRA", "size": "Large | 1050mm x 500mm", "color": "Granite", "base_price_rands": 1819.45, "stock_quantity": 0 },
        { "code": "PPROPP-LG-GRA-2", "size": "Large | 1050mm x 500mm", "color": "Granite Sealed", "base_price_rands": 1819.45, "stock_quantity": 0 },
        { "code": "PPROPP-LG-ROC", "size": "Large | 1050mm x 500mm", "color": "Rock", "base_price_rands": 1819.45, "stock_quantity": 0 },
        { "code": "PPROPP-LG-VEL", "size": "Large | 1050mm x 500mm", "color": "Velvet", "base_price_rands": 1819.45, "stock_quantity": 0 },
        { "code": "PPROPP-LG-CHR", "size": "Large | 1050mm x 500mm", "color": "Chryso Black", "base_price_rands": 1819.45, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Premium Windsor Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "PWINPP-SM-AMP", "size": "Small | 370mm x 240mm", "color": "Amper", "base_price_rands": 449.91, "stock_quantity": 0 },
        { "code": "PWINPP-SM-FWH", "size": "Small | 370mm x 240mm", "color": "Flinted White", "base_price_rands": 449.91, "stock_quantity": 0 },
        { "code": "PWINPP-SM-GRA", "size": "Small | 370mm x 240mm", "color": "Granite", "base_price_rands": 449.91, "stock_quantity": 0 },
        { "code": "PWINPP-SM-GRA-2", "size": "Small | 370mm x 240mm", "color": "Granite Sealed", "base_price_rands": 449.91, "stock_quantity": 0 },
        { "code": "PWINPP-SM-ROC", "size": "Small | 370mm x 240mm", "color": "Rock", "base_price_rands": 449.91, "stock_quantity": 0 },
        { "code": "PWINPP-SM-VEL", "size": "Small | 370mm x 240mm", "color": "Velvet", "base_price_rands": 449.91, "stock_quantity": 0 },
        { "code": "PWINPP-SM-CHR", "size": "Small | 370mm x 240mm", "color": "Chryso Black", "base_price_rands": 449.91, "stock_quantity": 0 },
        { "code": "PWINPP-MD-AMP", "size": "Medium | 530mm x 330mm", "color": "Amper", "base_price_rands": 879.82, "stock_quantity": 0 },
        { "code": "PWINPP-MD-FWH", "size": "Medium | 530mm x 330mm", "color": "Flinted White", "base_price_rands": 879.82, "stock_quantity": 0 },
        { "code": "PWINPP-MD-GRA", "size": "Medium | 530mm x 330mm", "color": "Granite", "base_price_rands": 879.82, "stock_quantity": 0 },
        { "code": "PWINPP-MD-GRA-2", "size": "Medium | 530mm x 330mm", "color": "Granite Sealed", "base_price_rands": 879.82, "stock_quantity": 0 },
        { "code": "PWINPP-MD-ROC", "size": "Medium | 530mm x 330mm", "color": "Rock", "base_price_rands": 879.82, "stock_quantity": 0 },
        { "code": "PWINPP-MD-VEL", "size": "Medium | 530mm x 330mm", "color": "Velvet", "base_price_rands": 879.82, "stock_quantity": 0 },
        { "code": "PWINPP-MD-CHR", "size": "Medium | 530mm x 330mm", "color": "Chryso Black", "base_price_rands": 879.82, "stock_quantity": 0 },
        { "code": "PWINPP-LG-AMP", "size": "Large | 650mm x 450mm", "color": "Amper", "base_price_rands": 1293.08, "stock_quantity": 0 },
        { "code": "PWINPP-LG-FWH", "size": "Large | 650mm x 450mm", "color": "Flinted White", "base_price_rands": 1293.08, "stock_quantity": 0 },
        { "code": "PWINPP-LG-GRA", "size": "Large | 650mm x 450mm", "color": "Granite", "base_price_rands": 1293.08, "stock_quantity": 0 },
        { "code": "PWINPP-LG-GRA-2", "size": "Large | 650mm x 450mm", "color": "Granite Sealed", "base_price_rands": 1293.08, "stock_quantity": 0 },
        { "code": "PWINPP-LG-ROC", "size": "Large | 650mm x 450mm", "color": "Rock", "base_price_rands": 1293.08, "stock_quantity": 0 },
        { "code": "PWINPP-LG-VEL", "size": "Large | 650mm x 450mm", "color": "Velvet", "base_price_rands": 1293.08, "stock_quantity": 0 },
        { "code": "PWINPP-LG-CHR", "size": "Large | 650mm x 450mm", "color": "Chryso Black", "base_price_rands": 1293.08, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Premium Colorado Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "PCOLPP-710-AMP", "size": "710mm x 590mm", "color": "Amper", "base_price_rands": 2438.19, "stock_quantity": 0 },
        { "code": "PCOLPP-710-FWH", "size": "710mm x 590mm", "color": "Flinted White", "base_price_rands": 2438.19, "stock_quantity": 0 },
        { "code": "PCOLPP-710-GRA", "size": "710mm x 590mm", "color": "Granite", "base_price_rands": 2438.19, "stock_quantity": 0 },
        { "code": "PCOLPP-710-GRA-2", "size": "710mm x 590mm", "color": "Granite Sealed", "base_price_rands": 2438.19, "stock_quantity": 0 },
        { "code": "PCOLPP-710-ROC", "size": "710mm x 590mm", "color": "Rock", "base_price_rands": 2438.19, "stock_quantity": 0 },
        { "code": "PCOLPP-710-VEL", "size": "710mm x 590mm", "color": "Velvet", "base_price_rands": 2438.19, "stock_quantity": 0 },
        { "code": "PCOLPP-710-CHR", "size": "710mm x 590mm", "color": "Chryso Black", "base_price_rands": 2438.19, "stock_quantity": 0 },
        { "code": "PCOLPP-710-BRO", "size": "710mm x 590mm", "color": "Bronze", "base_price_rands": 2438.19, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Premium Iris Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "PIRIPP-250-AMP", "size": "Tiny | 250mm x 210mm", "color": "Amper", "base_price_rands": 154.15, "stock_quantity": 0 },
        { "code": "PIRIPP-250-FWH", "size": "Tiny | 250mm x 210mm", "color": "Flinted White", "base_price_rands": 154.15, "stock_quantity": 0 },
        { "code": "PIRIPP-250-GRA", "size": "Tiny | 250mm x 210mm", "color": "Granite", "base_price_rands": 154.15, "stock_quantity": 0 },
        { "code": "PIRIPP-250-GRA-2", "size": "Tiny | 250mm x 210mm", "color": "Granite Sealed", "base_price_rands": 154.15, "stock_quantity": 0 },
        { "code": "PIRIPP-250-ROC", "size": "Tiny | 250mm x 210mm", "color": "Rock", "base_price_rands": 154.15, "stock_quantity": 0 },
        { "code": "PIRIPP-250-VEL", "size": "Tiny | 250mm x 210mm", "color": "Velvet", "base_price_rands": 154.15, "stock_quantity": 0 },
        { "code": "PIRIPP-250-CHR", "size": "Tiny | 250mm x 210mm", "color": "Chryso Black", "base_price_rands": 154.15, "stock_quantity": 0 },
        { "code": "PIRIPP-SM-AMP", "size": "Small | 500mm x 400mm", "color": "Amper", "base_price_rands": 589.9, "stock_quantity": 0 },
        { "code": "PIRIPP-SM-FWH", "size": "Small | 500mm x 400mm", "color": "Flinted White", "base_price_rands": 589.9, "stock_quantity": 0 },
        { "code": "PIRIPP-SM-GRA", "size": "Small | 500mm x 400mm", "color": "Granite", "base_price_rands": 589.9, "stock_quantity": 0 },
        { "code": "PIRIPP-SM-GRA-2", "size": "Small | 500mm x 400mm", "color": "Granite Sealed", "base_price_rands": 589.9, "stock_quantity": 0 },
        { "code": "PIRIPP-SM-ROC", "size": "Small | 500mm x 400mm", "color": "Rock", "base_price_rands": 589.9, "stock_quantity": 0 },
        { "code": "PIRIPP-SM-VEL", "size": "Small | 500mm x 400mm", "color": "Velvet", "base_price_rands": 589.9, "stock_quantity": 0 },
        { "code": "PIRIPP-SM-CHR", "size": "Small | 500mm x 400mm", "color": "Chryso Black", "base_price_rands": 589.9, "stock_quantity": 0 },
        { "code": "PIRIPP-MD-AMP", "size": "Medium | 630mm x 480mm", "color": "Amper", "base_price_rands": 1251.93, "stock_quantity": 0 },
        { "code": "PIRIPP-MD-FWH", "size": "Medium | 630mm x 480mm", "color": "Flinted White", "base_price_rands": 1251.93, "stock_quantity": 0 },
        { "code": "PIRIPP-MD-GRA", "size": "Medium | 630mm x 480mm", "color": "Granite", "base_price_rands": 1251.93, "stock_quantity": 0 },
        { "code": "PIRIPP-MD-GRA-2", "size": "Medium | 630mm x 480mm", "color": "Granite Sealed", "base_price_rands": 1251.93, "stock_quantity": 0 },
        { "code": "PIRIPP-MD-ROC", "size": "Medium | 630mm x 480mm", "color": "Rock", "base_price_rands": 1251.93, "stock_quantity": 0 },
        { "code": "PIRIPP-MD-VEL", "size": "Medium | 630mm x 480mm", "color": "Velvet", "base_price_rands": 1251.93, "stock_quantity": 0 },
        { "code": "PIRIPP-MD-CHR", "size": "Medium | 630mm x 480mm", "color": "Chryso Black", "base_price_rands": 1251.93, "stock_quantity": 0 },
        { "code": "PIRIPP-LG-AMP", "size": "Large | 850mm x 500mm", "color": "Amper", "base_price_rands": 1734.47, "stock_quantity": 0 },
        { "code": "PIRIPP-LG-FWH", "size": "Large | 850mm x 500mm", "color": "Flinted White", "base_price_rands": 1734.47, "stock_quantity": 0 },
        { "code": "PIRIPP-LG-GRA", "size": "Large | 850mm x 500mm", "color": "Granite", "base_price_rands": 1734.47, "stock_quantity": 0 },
        { "code": "PIRIPP-LG-GRA-2", "size": "Large | 850mm x 500mm", "color": "Granite Sealed", "base_price_rands": 1734.47, "stock_quantity": 0 },
        { "code": "PIRIPP-LG-ROC", "size": "Large | 850mm x 500mm", "color": "Rock", "base_price_rands": 1734.47, "stock_quantity": 0 },
        { "code": "PIRIPP-LG-VEL", "size": "Large | 850mm x 500mm", "color": "Velvet", "base_price_rands": 1734.47, "stock_quantity": 0 },
        { "code": "PIRIPP-LG-CHR", "size": "Large | 850mm x 500mm", "color": "Chryso Black", "base_price_rands": 1734.47, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Premium Delia Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "PDELPP-SM-AMP", "size": "Small | 640mm X 240mm", "color": "Amper", "base_price_rands": 608.83, "stock_quantity": 0 },
        { "code": "PDELPP-SM-FWH", "size": "Small | 640mm X 240mm", "color": "Flinted White", "base_price_rands": 608.83, "stock_quantity": 0 },
        { "code": "PDELPP-SM-GRA", "size": "Small | 640mm X 240mm", "color": "Granite", "base_price_rands": 608.83, "stock_quantity": 0 },
        { "code": "PDELPP-SM-GRA-2", "size": "Small | 640mm X 240mm", "color": "Granite Sealed", "base_price_rands": 608.83, "stock_quantity": 0 },
        { "code": "PDELPP-SM-ROC", "size": "Small | 640mm X 240mm", "color": "Rock", "base_price_rands": 608.83, "stock_quantity": 0 },
        { "code": "PDELPP-SM-VEL", "size": "Small | 640mm X 240mm", "color": "Velvet", "base_price_rands": 608.83, "stock_quantity": 0 },
        { "code": "PDELPP-SM-CHR", "size": "Small | 640mm X 240mm", "color": "Chryso Black", "base_price_rands": 608.83, "stock_quantity": 0 },
        { "code": "PDELPP-MD-AMP", "size": "Medium | 790mm X 440mm", "color": "Amper", "base_price_rands": 1304.62, "stock_quantity": 0 },
        { "code": "PDELPP-MD-FWH", "size": "Medium | 790mm X 440mm", "color": "Flinted White", "base_price_rands": 1304.62, "stock_quantity": 0 },
        { "code": "PDELPP-MD-GRA", "size": "Medium | 790mm X 440mm", "color": "Granite", "base_price_rands": 1304.62, "stock_quantity": 0 },
        { "code": "PDELPP-MD-GRA-2", "size": "Medium | 790mm X 440mm", "color": "Granite Sealed", "base_price_rands": 1304.62, "stock_quantity": 0 },
        { "code": "PDELPP-MD-ROC", "size": "Medium | 790mm X 440mm", "color": "Rock", "base_price_rands": 1304.62, "stock_quantity": 0 },
        { "code": "PDELPP-MD-VEL", "size": "Medium | 790mm X 440mm", "color": "Velvet", "base_price_rands": 1304.62, "stock_quantity": 0 },
        { "code": "PDELPP-MD-CHR", "size": "Medium | 790mm X 440mm", "color": "Chryso Black", "base_price_rands": 1304.62, "stock_quantity": 0 },
        { "code": "PDELPP-LG-AMP", "size": "Large | 900mm X 450mm", "color": "Amper", "base_price_rands": 1696.01, "stock_quantity": 0 },
        { "code": "PDELPP-LG-FWH", "size": "Large | 900mm X 450mm", "color": "Flinted White", "base_price_rands": 1696.01, "stock_quantity": 0 },
        { "code": "PDELPP-LG-GRA", "size": "Large | 900mm X 450mm", "color": "Granite", "base_price_rands": 1696.01, "stock_quantity": 0 },
        { "code": "PDELPP-LG-GRA-2", "size": "Large | 900mm X 450mm", "color": "Granite Sealed", "base_price_rands": 1696.01, "stock_quantity": 0 },
        { "code": "PDELPP-LG-ROC", "size": "Large | 900mm X 450mm", "color": "Rock", "base_price_rands": 1696.01, "stock_quantity": 0 },
        { "code": "PDELPP-LG-VEL", "size": "Large | 900mm X 450mm", "color": "Velvet", "base_price_rands": 1696.01, "stock_quantity": 0 },
        { "code": "PDELPP-LG-CHR", "size": "Large | 900mm X 450mm", "color": "Chryso Black", "base_price_rands": 1696.01, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Premium Eggin Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "PEGGPP-270-ROC", "size": "Mini | 270mm X 230mm", "color": "Rock", "base_price_rands": 217.44, "stock_quantity": 0 },
        { "code": "PEGGPP-270-GRA", "size": "Mini | 270mm X 230mm", "color": "Granite", "base_price_rands": 217.44, "stock_quantity": 0 },
        { "code": "PEGGPP-270-GRA-2", "size": "Mini | 270mm X 230mm", "color": "Granite Sealed", "base_price_rands": 217.44, "stock_quantity": 0 },
        { "code": "PEGGPP-270-AMP", "size": "Mini | 270mm X 230mm", "color": "Amper", "base_price_rands": 217.44, "stock_quantity": 0 },
        { "code": "PEGGPP-270-VEL", "size": "Mini | 270mm X 230mm", "color": "Velvet", "base_price_rands": 217.44, "stock_quantity": 0 },
        { "code": "PEGGPP-270-FWH", "size": "Mini | 270mm X 230mm", "color": "Flinted White", "base_price_rands": 217.44, "stock_quantity": 0 },
        { "code": "PEGGPP-270-CHR", "size": "Mini | 270mm X 230mm", "color": "Chryso Black", "base_price_rands": 217.44, "stock_quantity": 0 },
        { "code": "PEGGPP-SM-ROC", "size": "Small | 450mm X 330mm", "color": "Rock", "base_price_rands": 521.85, "stock_quantity": 0 },
        { "code": "PEGGPP-SM-GRA", "size": "Small | 450mm X 330mm", "color": "Granite", "base_price_rands": 521.85, "stock_quantity": 0 },
        { "code": "PEGGPP-SM-GRA-2", "size": "Small | 450mm X 330mm", "color": "Granite Sealed", "base_price_rands": 521.85, "stock_quantity": 0 },
        { "code": "PEGGPP-SM-AMP", "size": "Small | 450mm X 330mm", "color": "Amper", "base_price_rands": 521.85, "stock_quantity": 0 },
        { "code": "PEGGPP-SM-VEL", "size": "Small | 450mm X 330mm", "color": "Velvet", "base_price_rands": 521.85, "stock_quantity": 0 },
        { "code": "PEGGPP-SM-FWH", "size": "Small | 450mm X 330mm", "color": "Flinted White", "base_price_rands": 521.85, "stock_quantity": 0 },
        { "code": "PEGGPP-SM-CHR", "size": "Small | 450mm X 330mm", "color": "Chryso Black", "base_price_rands": 521.85, "stock_quantity": 0 },
        { "code": "PEGGPP-MD-ROC", "size": "Medium", "color": "Rock", "base_price_rands": 913.23, "stock_quantity": 0 },
        { "code": "PEGGPP-MD-GRA", "size": "Medium", "color": "Granite", "base_price_rands": 913.23, "stock_quantity": 0 },
        { "code": "PEGGPP-MD-GRA-2", "size": "Medium", "color": "Granite Sealed", "base_price_rands": 913.23, "stock_quantity": 0 },
        { "code": "PEGGPP-MD-AMP", "size": "Medium", "color": "Amper", "base_price_rands": 913.23, "stock_quantity": 0 },
        { "code": "PEGGPP-MD-VEL", "size": "Medium", "color": "Velvet", "base_price_rands": 913.23, "stock_quantity": 0 },
        { "code": "PEGGPP-MD-FWH", "size": "Medium", "color": "Flinted White", "base_price_rands": 913.23, "stock_quantity": 0 },
        { "code": "PEGGPP-MD-CHR", "size": "Medium", "color": "Chryso Black", "base_price_rands": 913.23, "stock_quantity": 0 },
        { "code": "PEGGPP-LG-ROC", "size": "Large | 850mm X 580mm", "color": "Rock", "base_price_rands": 1782.98, "stock_quantity": 0 },
        { "code": "PEGGPP-LG-GRA", "size": "Large | 850mm X 580mm", "color": "Granite", "base_price_rands": 1782.98, "stock_quantity": 0 },
        { "code": "PEGGPP-LG-GRA-2", "size": "Large | 850mm X 580mm", "color": "Granite Sealed", "base_price_rands": 1782.98, "stock_quantity": 0 },
        { "code": "PEGGPP-LG-AMP", "size": "Large | 850mm X 580mm", "color": "Amper", "base_price_rands": 1782.98, "stock_quantity": 0 },
        { "code": "PEGGPP-LG-VEL", "size": "Large | 850mm X 580mm", "color": "Velvet", "base_price_rands": 1782.98, "stock_quantity": 0 },
        { "code": "PEGGPP-LG-FWH", "size": "Large | 850mm X 580mm", "color": "Flinted White", "base_price_rands": 1782.98, "stock_quantity": 0 },
        { "code": "PEGGPP-LG-CHR", "size": "Large | 850mm X 580mm", "color": "Chryso Black", "base_price_rands": 1782.98, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Premium Curo Trough Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "PCURTRPP-SM-ROC", "size": "Small | 250mm h x 200mm w x 700mm l", "color": "rock", "base_price_rands": 976.53, "stock_quantity": 0 },
        { "code": "PCURTRPP-SM-GRA", "size": "Small | 250mm h x 200mm w x 700mm l", "color": "granite", "base_price_rands": 976.53, "stock_quantity": 0 },
        { "code": "PCURTRPP-SM-GRA-2", "size": "Small | 250mm h x 200mm w x 700mm l", "color": "Granite Sealed", "base_price_rands": 976.53, "stock_quantity": 0 },
        { "code": "PCURTRPP-SM-VEL", "size": "Small | 250mm h x 200mm w x 700mm l", "color": "Velvet", "base_price_rands": 976.53, "stock_quantity": 0 },
        { "code": "PCURTRPP-SM-AMP", "size": "Small | 250mm h x 200mm w x 700mm l", "color": "amper", "base_price_rands": 976.53, "stock_quantity": 0 },
        { "code": "PCURTRPP-SM-FWH", "size": "Small | 250mm h x 200mm w x 700mm l", "color": "Flinted White", "base_price_rands": 976.53, "stock_quantity": 0 },
        { "code": "PCURTRPP-SM-CHR", "size": "Small | 250mm h x 200mm w x 700mm l", "color": "Chryso Black", "base_price_rands": 976.53, "stock_quantity": 0 },
        { "code": "PCURTRPP-MD-ROC", "size": "Medium | 370mm h x 200mm w x 1160mm l", "color": "rock", "base_price_rands": 1664.29, "stock_quantity": 0 },
        { "code": "PCURTRPP-MD-GRA", "size": "Medium | 370mm h x 200mm w x 1160mm l", "color": "granite", "base_price_rands": 1664.29, "stock_quantity": 0 },
        { "code": "PCURTRPP-MD-GRA-2", "size": "Medium | 370mm h x 200mm w x 1160mm l", "color": "Granite Sealed", "base_price_rands": 1664.29, "stock_quantity": 0 },
        { "code": "PCURTRPP-MD-VEL", "size": "Medium | 370mm h x 200mm w x 1160mm l", "color": "Velvet", "base_price_rands": 1664.29, "stock_quantity": 0 },
        { "code": "PCURTRPP-MD-AMP", "size": "Medium | 370mm h x 200mm w x 1160mm l", "color": "amper", "base_price_rands": 1664.29, "stock_quantity": 0 },
        { "code": "PCURTRPP-MD-FWH", "size": "Medium | 370mm h x 200mm w x 1160mm l", "color": "Flinted White", "base_price_rands": 1664.29, "stock_quantity": 0 },
        { "code": "PCURTRPP-MD-CHR", "size": "Medium | 370mm h x 200mm w x 1160mm l", "color": "Chryso Black", "base_price_rands": 1664.29, "stock_quantity": 0 },
        { "code": "PCURTRPP-LG-ROC", "size": "Large | 370mmh x 400mmw x 1160mml", "color": "rock", "base_price_rands": 2325.46, "stock_quantity": 0 },
        { "code": "PCURTRPP-LG-GRA", "size": "Large | 370mmh x 400mmw x 1160mml", "color": "granite", "base_price_rands": 2325.46, "stock_quantity": 0 },
        { "code": "PCURTRPP-LG-GRA-2", "size": "Large | 370mmh x 400mmw x 1160mml", "color": "Granite Sealed", "base_price_rands": 2325.46, "stock_quantity": 0 },
        { "code": "PCURTRPP-LG-VEL", "size": "Large | 370mmh x 400mmw x 1160mml", "color": "Velvet", "base_price_rands": 2325.46, "stock_quantity": 0 },
        { "code": "PCURTRPP-LG-AMP", "size": "Large | 370mmh x 400mmw x 1160mml", "color": "amper", "base_price_rands": 2325.46, "stock_quantity": 0 },
        { "code": "PCURTRPP-LG-FWH", "size": "Large | 370mmh x 400mmw x 1160mml", "color": "Flinted White", "base_price_rands": 2325.46, "stock_quantity": 0 },
        { "code": "PCURTRPP-LG-CHR", "size": "Large | 370mmh x 400mmw x 1160mml", "color": "Chryso Black", "base_price_rands": 2325.46, "stock_quantity": 0 },
        { "code": "PCURTRPP-XL-ROC", "size": "Extra Large | 500mm h x 400mm w x 1160mml", "color": "rock", "base_price_rands": 2633.25, "stock_quantity": 0 },
        { "code": "PCURTRPP-XL-GRA", "size": "Extra Large | 500mm h x 400mm w x 1160mml", "color": "granite", "base_price_rands": 2633.25, "stock_quantity": 0 },
        { "code": "PCURTRPP-XL-GRA-2", "size": "Extra Large | 500mm h x 400mm w x 1160mml", "color": "Granite Sealed", "base_price_rands": 2633.25, "stock_quantity": 0 },
        { "code": "PCURTRPP-XL-VEL", "size": "Extra Large | 500mm h x 400mm w x 1160mml", "color": "Velvet", "base_price_rands": 2633.25, "stock_quantity": 0 },
        { "code": "PCURTRPP-XL-AMP", "size": "Extra Large | 500mm h x 400mm w x 1160mml", "color": "amper", "base_price_rands": 2633.25, "stock_quantity": 0 },
        { "code": "PCURTRPP-XL-FWH", "size": "Extra Large | 500mm h x 400mm w x 1160mml", "color": "Flinted White", "base_price_rands": 2633.25, "stock_quantity": 0 },
        { "code": "PCURTRPP-XL-CHR", "size": "Extra Large | 500mm h x 400mm w x 1160mml", "color": "Chryso Black", "base_price_rands": 2633.25, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Premium Egg Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "PEGGPP-SM-CHR-2", "size": "Small | 345mm x 395mm", "color": "Chryso Black", "base_price_rands": 539.59, "stock_quantity": 0 },
        { "code": "PEGGPP-SM-ROC-2", "size": "Small | 345mm x 395mm", "color": "Rock", "base_price_rands": 539.59, "stock_quantity": 0 },
        { "code": "PEGGPP-SM-GRA-3", "size": "Small | 345mm x 395mm", "color": "Granite", "base_price_rands": 539.59, "stock_quantity": 0 },
        { "code": "PEGGPP-SM-GRA-4", "size": "Small | 345mm x 395mm", "color": "Granite Sealed", "base_price_rands": 539.59, "stock_quantity": 0 },
        { "code": "PEGGPP-SM-VEL-2", "size": "Small | 345mm x 395mm", "color": "Velvet", "base_price_rands": 539.59, "stock_quantity": 0 },
        { "code": "PEGGPP-SM-AMP-2", "size": "Small | 345mm x 395mm", "color": "Ampler", "base_price_rands": 539.59, "stock_quantity": 0 },
        { "code": "PEGGPP-SM-FWH-2", "size": "Small | 345mm x 395mm", "color": "Flinted White", "base_price_rands": 539.59, "stock_quantity": 0 },
        { "code": "PEGGPP-MD-CHR-2", "size": "Medium | 430mm x 485mm", "color": "Chryso Black", "base_price_rands": 860.6, "stock_quantity": 0 },
        { "code": "PEGGPP-MD-ROC-2", "size": "Medium | 430mm x 485mm", "color": "Rock", "base_price_rands": 860.6, "stock_quantity": 0 },
        { "code": "PEGGPP-MD-GRA-3", "size": "Medium | 430mm x 485mm", "color": "Granite", "base_price_rands": 860.6, "stock_quantity": 0 },
        { "code": "PEGGPP-MD-GRA-4", "size": "Medium | 430mm x 485mm", "color": "Granite Sealed", "base_price_rands": 860.6, "stock_quantity": 0 },
        { "code": "PEGGPP-MD-VEL-2", "size": "Medium | 430mm x 485mm", "color": "Velvet", "base_price_rands": 860.6, "stock_quantity": 0 },
        { "code": "PEGGPP-MD-AMP-2", "size": "Medium | 430mm x 485mm", "color": "Ampler", "base_price_rands": 860.6, "stock_quantity": 0 },
        { "code": "PEGGPP-MD-FWH-2", "size": "Medium | 430mm x 485mm", "color": "Flinted White", "base_price_rands": 860.6, "stock_quantity": 0 },
        { "code": "PEGGPP-LG-CHR-2", "size": "Large | 510mm x 600mm", "color": "Chryso Black", "base_price_rands": 1410.49, "stock_quantity": 0 },
        { "code": "PEGGPP-LG-ROC-2", "size": "Large | 510mm x 600mm", "color": "Rock", "base_price_rands": 1410.49, "stock_quantity": 0 },
        { "code": "PEGGPP-LG-GRA-3", "size": "Large | 510mm x 600mm", "color": "Granite", "base_price_rands": 1410.49, "stock_quantity": 0 },
        { "code": "PEGGPP-LG-GRA-4", "size": "Large | 510mm x 600mm", "color": "Granite Sealed", "base_price_rands": 1410.49, "stock_quantity": 0 },
        { "code": "PEGGPP-LG-VEL-2", "size": "Large | 510mm x 600mm", "color": "Velvet", "base_price_rands": 1410.49, "stock_quantity": 0 },
        { "code": "PEGGPP-LG-AMP-2", "size": "Large | 510mm x 600mm", "color": "Ampler", "base_price_rands": 1410.49, "stock_quantity": 0 },
        { "code": "PEGGPP-LG-FWH-2", "size": "Large | 510mm x 600mm", "color": "Flinted White", "base_price_rands": 1410.49, "stock_quantity": 0 },
        { "code": "PEGGPP-610-CHR", "size": "Jumbo | 610mm x 770mm", "color": "Chryso Black", "base_price_rands": 2227.93, "stock_quantity": 0 },
        { "code": "PEGGPP-610-ROC", "size": "Jumbo | 610mm x 770mm", "color": "Rock", "base_price_rands": 2227.93, "stock_quantity": 0 },
        { "code": "PEGGPP-610-GRA", "size": "Jumbo | 610mm x 770mm", "color": "Granite", "base_price_rands": 2227.93, "stock_quantity": 0 },
        { "code": "PEGGPP-610-GRA-2", "size": "Jumbo | 610mm x 770mm", "color": "Granite Sealed", "base_price_rands": 2227.93, "stock_quantity": 0 },
        { "code": "PEGGPP-610-VEL", "size": "Jumbo | 610mm x 770mm", "color": "Velvet", "base_price_rands": 2227.93, "stock_quantity": 0 },
        { "code": "PEGGPP-610-AMP", "size": "Jumbo | 610mm x 770mm", "color": "Ampler", "base_price_rands": 2227.93, "stock_quantity": 0 },
        { "code": "PEGGPP-610-FWH", "size": "Jumbo | 610mm x 770mm", "color": "Flinted White", "base_price_rands": 2227.93, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Tudor Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "TUDPP-LG-FWH", "size": "Large | 410mm x 410mm", "color": "flinted white", "base_price_rands": 1086.47, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Symphony Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "SYMPP-LG-FWH", "size": "Large | 460mm x 550mm", "color": "flinted white", "base_price_rands": 1229.77, "stock_quantity": 0 }
      ]
    },
    {
      "name": "African Urn concrete pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "AFRURN-Jumbo-AMP", "size": "Jumbo", "color": "Amper", "base_price_rands": 1734.53, "stock_quantity": 0 },
        { "code": "AFRURN-Jumbo-FWH", "size": "Jumbo", "color": "Flinted White", "base_price_rands": 1734.53, "stock_quantity": 0 },
        { "code": "AFRURN-Jumbo-GRA", "size": "Jumbo", "color": "Granite", "base_price_rands": 1734.53, "stock_quantity": 0 },
        { "code": "AFRURN-Jumbo-GRA-2", "size": "Jumbo", "color": "Granite Sealed", "base_price_rands": 1734.53, "stock_quantity": 0 },
        { "code": "AFRURN-Jumbo-ROC", "size": "Jumbo", "color": "Rock", "base_price_rands": 1734.53, "stock_quantity": 0 },
        { "code": "AFRURN-Jumbo-VEL", "size": "Jumbo", "color": "Velvet", "base_price_rands": 1734.53, "stock_quantity": 0 },
        { "code": "AFRURN-Jumbo-CHR", "size": "Jumbo", "color": "Chryso Black", "base_price_rands": 1734.53, "stock_quantity": 0 },
        { "code": "AFRURN-LG-AMP", "size": "Large", "color": "Amper", "base_price_rands": 1178.62, "stock_quantity": 0 },
        { "code": "AFRURN-LG-FWH", "size": "Large", "color": "Flinted White", "base_price_rands": 1178.62, "stock_quantity": 0 },
        { "code": "AFRURN-LG-GRA", "size": "Large", "color": "Granite", "base_price_rands": 1178.62, "stock_quantity": 0 },
        { "code": "AFRURN-LG-GRA-2", "size": "Large", "color": "Granite Sealed", "base_price_rands": 1178.62, "stock_quantity": 0 },
        { "code": "AFRURN-LG-ROC", "size": "Large", "color": "Rock", "base_price_rands": 1178.62, "stock_quantity": 0 },
        { "code": "AFRURN-LG-VEL", "size": "Large", "color": "Velvet", "base_price_rands": 1178.62, "stock_quantity": 0 },
        { "code": "AFRURN-LG-CHR", "size": "Large", "color": "Chryso Black", "base_price_rands": 1734.53, "stock_quantity": 0 },
        { "code": "AFRURN-MD-AMP", "size": "Medium", "color": "Amper", "base_price_rands": 653.42, "stock_quantity": 0 },
        { "code": "AFRURN-MD-FWH", "size": "Medium", "color": "Flinted White", "base_price_rands": 653.42, "stock_quantity": 0 },
        { "code": "AFRURN-MD-GRA", "size": "Medium", "color": "Granite", "base_price_rands": 653.42, "stock_quantity": 0 },
        { "code": "AFRURN-MD-GRA-2", "size": "Medium", "color": "Granite Sealed", "base_price_rands": 653.42, "stock_quantity": 0 },
        { "code": "AFRURN-MD-ROC", "size": "Medium", "color": "Rock", "base_price_rands": 653.42, "stock_quantity": 0 },
        { "code": "AFRURN-MD-VEL", "size": "Medium", "color": "Velvet", "base_price_rands": 653.42, "stock_quantity": 0 },
        { "code": "AFRURN-MD-CHR", "size": "Medium", "color": "Chryso Black", "base_price_rands": 1734.53, "stock_quantity": 0 },
        { "code": "AFRURN-SM-AMP", "size": "Small", "color": "Amper", "base_price_rands": 478.5, "stock_quantity": 0 },
        { "code": "AFRURN-SM-FWH", "size": "Small", "color": "Flinted White", "base_price_rands": 478.5, "stock_quantity": 0 },
        { "code": "AFRURN-SM-GRA", "size": "Small", "color": "Granite", "base_price_rands": 478.5, "stock_quantity": 0 },
        { "code": "AFRURN-SM-GRA-2", "size": "Small", "color": "Granite Sealed", "base_price_rands": 478.5, "stock_quantity": 0 },
        { "code": "AFRURN-SM-ROC", "size": "Small", "color": "Rock", "base_price_rands": 478.5, "stock_quantity": 0 },
        { "code": "AFRURN-SM-VEL", "size": "Small", "color": "Velvet", "base_price_rands": 478.5, "stock_quantity": 0 },
        { "code": "AFRURN-SM-CHR", "size": "Small", "color": "Chryso Black", "base_price_rands": 1734.53, "stock_quantity": 0 }
      ]
    },
    {
      "name": "G/S Trough Tray",
      "category": "Concrete Tray",
      "description_html": "",
      "skus": [
        { "code": "GSTRTY-LG-AMP", "size": "Large", "color": "Amper", "base_price_rands": 669.85, "stock_quantity": 0 },
        { "code": "GSTRTY-LG-FWH", "size": "Large", "color": "Flinted White", "base_price_rands": 669.85, "stock_quantity": 0 },
        { "code": "GSTRTY-LG-GRA", "size": "Large", "color": "Granite", "base_price_rands": 669.85, "stock_quantity": 0 },
        { "code": "GSTRTY-LG-GRA-2", "size": "Large", "color": "Granite Sealed", "base_price_rands": 669.85, "stock_quantity": 0 },
        { "code": "GSTRTY-LG-ROC", "size": "Large", "color": "Rock", "base_price_rands": 669.85, "stock_quantity": 0 },
        { "code": "GSTRTY-LG-VEL", "size": "Large", "color": "Velvet", "base_price_rands": 669.85, "stock_quantity": 0 },
        { "code": "GSTRTY-LG-CHR", "size": "Large", "color": "Chryso Black", "base_price_rands": 669.85, "stock_quantity": 0 },
        { "code": "GSTRTY-MD-AMP", "size": "Medium", "color": "Amper", "base_price_rands": 463.24, "stock_quantity": 0 },
        { "code": "GSTRTY-MD-FWH", "size": "Medium", "color": "Flinted White", "base_price_rands": 463.24, "stock_quantity": 0 },
        { "code": "GSTRTY-MD-GRA", "size": "Medium", "color": "Granite", "base_price_rands": 463.24, "stock_quantity": 0 },
        { "code": "GSTRTY-MD-GRA-2", "size": "Medium", "color": "Granite Sealed", "base_price_rands": 463.24, "stock_quantity": 0 },
        { "code": "GSTRTY-MD-ROC", "size": "Medium", "color": "Rock", "base_price_rands": 463.24, "stock_quantity": 0 },
        { "code": "GSTRTY-MD-VEL", "size": "Medium", "color": "Velvet", "base_price_rands": 463.24, "stock_quantity": 0 },
        { "code": "GSTRTY-MD-CHR", "size": "Medium", "color": "Chryso Black", "base_price_rands": 463.24, "stock_quantity": 0 },
        { "code": "GSTRTY-SM-AMP", "size": "Small", "color": "Amper", "base_price_rands": 343.25, "stock_quantity": 0 },
        { "code": "GSTRTY-SM-FWH", "size": "Small", "color": "Flinted White", "base_price_rands": 343.25, "stock_quantity": 0 },
        { "code": "GSTRTY-SM-GRA", "size": "Small", "color": "Granite", "base_price_rands": 343.25, "stock_quantity": 0 },
        { "code": "GSTRTY-SM-GRA-2", "size": "Small", "color": "Granite Sealed", "base_price_rands": 343.25, "stock_quantity": 0 },
        { "code": "GSTRTY-SM-ROC", "size": "Small", "color": "Rock", "base_price_rands": 343.25, "stock_quantity": 0 },
        { "code": "GSTRTY-SM-VEL", "size": "Small", "color": "Velvet", "base_price_rands": 343.25, "stock_quantity": 0 },
        { "code": "GSTRTY-SM-CHR", "size": "Small", "color": "Chryso Black", "base_price_rands": 343.25, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Curo Trough Tray",
      "category": "Concrete Tray",
      "description_html": "",
      "skus": [
        { "code": "CURTRTY-LG-AMP", "size": "Large | 1170mm x 425mm", "color": "Amper", "base_price_rands": 629.83, "stock_quantity": 0 },
        { "code": "CURTRTY-LG-FWH", "size": "Large | 1170mm x 425mm", "color": "Flinted White", "base_price_rands": 629.83, "stock_quantity": 0 },
        { "code": "CURTRTY-LG-GRA", "size": "Large | 1170mm x 425mm", "color": "Granite", "base_price_rands": 629.83, "stock_quantity": 0 },
        { "code": "CURTRTY-LG-GRA-2", "size": "Large | 1170mm x 425mm", "color": "Granite Sealed", "base_price_rands": 629.83, "stock_quantity": 0 },
        { "code": "CURTRTY-LG-ROC", "size": "Large | 1170mm x 425mm", "color": "Rock", "base_price_rands": 629.83, "stock_quantity": 0 },
        { "code": "CURTRTY-LG-VEL", "size": "Large | 1170mm x 425mm", "color": "Velvet", "base_price_rands": 629.83, "stock_quantity": 0 },
        { "code": "CURTRTY-LG-CHR", "size": "Large | 1170mm x 425mm", "color": "Chryso Black", "base_price_rands": 629.83, "stock_quantity": 0 },
        { "code": "CURTRTY-MD-AMP", "size": "Medium", "color": "Amper", "base_price_rands": 543.0, "stock_quantity": 0 },
        { "code": "CURTRTY-MD-FWH", "size": "Medium", "color": "Flinted White", "base_price_rands": 543.0, "stock_quantity": 0 },
        { "code": "CURTRTY-MD-GRA", "size": "Medium", "color": "Granite", "base_price_rands": 543.0, "stock_quantity": 0 },
        { "code": "CURTRTY-MD-GRA-2", "size": "Medium", "color": "Granite Sealed", "base_price_rands": 543.0, "stock_quantity": 0 },
        { "code": "CURTRTY-MD-ROC", "size": "Medium", "color": "Rock", "base_price_rands": 543.0, "stock_quantity": 0 },
        { "code": "CURTRTY-MD-VEL", "size": "Medium", "color": "Velvet", "base_price_rands": 543.0, "stock_quantity": 0 },
        { "code": "CURTRTY-MD-CHR", "size": "Medium", "color": "Chryso Black", "base_price_rands": 543.0, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Tulip Trough Tray",
      "category": "Concrete Tray",
      "description_html": "",
      "skus": [
        { "code": "TULTRTY-LG-AMP", "size": "Large | 620mm x 240mm", "color": "Amper", "base_price_rands": 408.62, "stock_quantity": 0 },
        { "code": "TULTRTY-LG-FWH", "size": "Large | 620mm x 240mm", "color": "Flinted White", "base_price_rands": 408.62, "stock_quantity": 0 },
        { "code": "TULTRTY-LG-GRA", "size": "Large | 620mm x 240mm", "color": "Granite", "base_price_rands": 408.62, "stock_quantity": 0 },
        { "code": "TULTRTY-LG-GRA-2", "size": "Large | 620mm x 240mm", "color": "Granite Sealed", "base_price_rands": 408.62, "stock_quantity": 0 },
        { "code": "TULTRTY-LG-ROC", "size": "Large | 620mm x 240mm", "color": "Rock", "base_price_rands": 408.62, "stock_quantity": 0 },
        { "code": "TULTRTY-LG-VEL", "size": "Large | 620mm x 240mm", "color": "Velvet", "base_price_rands": 408.62, "stock_quantity": 0 },
        { "code": "TULTRTY-LG-CHR", "size": "Large | 620mm x 240mm", "color": "Chryso Black", "base_price_rands": 408.62, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Drip Tray",
      "category": "Concrete Tray",
      "description_html": "",
      "skus": [
        { "code": "DRITY-LG-AMP", "size": "Large | 380mm", "color": "Amper", "base_price_rands": 129.85, "stock_quantity": 0 },
        { "code": "DRITY-LG-FWH", "size": "Large | 380mm", "color": "Flinted White", "base_price_rands": 129.85, "stock_quantity": 0 },
        { "code": "DRITY-LG-GRL", "size": "Large | 380mm", "color": "Granite light", "base_price_rands": 129.85, "stock_quantity": 0 },
        { "code": "DRITY-LG-GRA", "size": "Large | 380mm", "color": "Granite Dark Sealed", "base_price_rands": 129.85, "stock_quantity": 0 },
        { "code": "DRITY-LG-ROC", "size": "Large | 380mm", "color": "Rock", "base_price_rands": 129.85, "stock_quantity": 0 },
        { "code": "DRITY-LG-VEL", "size": "Large | 380mm", "color": "Velvet", "base_price_rands": 129.85, "stock_quantity": 0 },
        { "code": "DRITY-MD-AMP", "size": "Medium | 330mm", "color": "Amper", "base_price_rands": 113.63, "stock_quantity": 0 },
        { "code": "DRITY-MD-FWH", "size": "Medium | 330mm", "color": "Flinted White", "base_price_rands": 113.63, "stock_quantity": 0 },
        { "code": "DRITY-MD-GRL", "size": "Medium | 330mm", "color": "Granite light", "base_price_rands": 113.63, "stock_quantity": 0 },
        { "code": "DRITY-MD-GRA", "size": "Medium | 330mm", "color": "Granite Dark Sealed", "base_price_rands": 113.63, "stock_quantity": 0 },
        { "code": "DRITY-MD-ROC", "size": "Medium | 330mm", "color": "Rock", "base_price_rands": 113.63, "stock_quantity": 0 },
        { "code": "DRITY-MD-VEL", "size": "Medium | 330mm", "color": "Velvet", "base_price_rands": 113.63, "stock_quantity": 0 },
        { "code": "DRITY-SM-AMP", "size": "Small | 240mm", "color": "Amper", "base_price_rands": 64.93, "stock_quantity": 0 },
        { "code": "DRITY-SM-FWH", "size": "Small | 240mm", "color": "Flinted White", "base_price_rands": 64.93, "stock_quantity": 0 },
        { "code": "DRITY-SM-GRL", "size": "Small | 240mm", "color": "Granite light", "base_price_rands": 64.93, "stock_quantity": 0 },
        { "code": "DRITY-SM-GRA", "size": "Small | 240mm", "color": "Granite Dark Sealed", "base_price_rands": 64.93, "stock_quantity": 0 },
        { "code": "DRITY-SM-ROC", "size": "Small | 240mm", "color": "Rock", "base_price_rands": 64.93, "stock_quantity": 0 },
        { "code": "DRITY-SM-VEL", "size": "Small | 240mm", "color": "Velvet", "base_price_rands": 64.93, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Square Tray",
      "category": "Concrete Tray",
      "description_html": "",
      "skus": [
        { "code": "SQUTY-LG-AMP", "size": "Large | 600mm", "color": "Amper", "base_price_rands": 250.88, "stock_quantity": 0 },
        { "code": "SQUTY-LG-FWH", "size": "Large | 600mm", "color": "Flinted White", "base_price_rands": 250.88, "stock_quantity": 0 },
        { "code": "SQUTY-LG-GRA", "size": "Large | 600mm", "color": "Granite", "base_price_rands": 250.88, "stock_quantity": 0 },
        { "code": "SQUTY-LG-GRA-2", "size": "Large | 600mm", "color": "Granite Sealed", "base_price_rands": 250.88, "stock_quantity": 0 },
        { "code": "SQUTY-LG-ROC", "size": "Large | 600mm", "color": "Rock", "base_price_rands": 250.88, "stock_quantity": 0 },
        { "code": "SQUTY-LG-VEL", "size": "Large | 600mm", "color": "Velvet", "base_price_rands": 250.88, "stock_quantity": 0 },
        { "code": "SQUTY-LG-CHR", "size": "Large | 600mm", "color": "Chryso Black", "base_price_rands": 250.88, "stock_quantity": 0 },
        { "code": "SQUTY-400-AMP", "size": "ST | 400mm", "color": "Amper", "base_price_rands": 498.35, "stock_quantity": 0 },
        { "code": "SQUTY-400-FWH", "size": "ST | 400mm", "color": "Flinted White", "base_price_rands": 498.35, "stock_quantity": 0 },
        { "code": "SQUTY-400-GRA", "size": "ST | 400mm", "color": "Granite", "base_price_rands": 498.35, "stock_quantity": 0 },
        { "code": "SQUTY-400-GRA-2", "size": "ST | 400mm", "color": "Granite Sealed", "base_price_rands": 498.35, "stock_quantity": 0 },
        { "code": "SQUTY-400-ROC", "size": "ST | 400mm", "color": "Rock", "base_price_rands": 498.35, "stock_quantity": 0 },
        { "code": "SQUTY-400-VEL", "size": "ST | 400mm", "color": "Velvet", "base_price_rands": 498.35, "stock_quantity": 0 },
        { "code": "SQUTY-400-CHR", "size": "ST | 400mm", "color": "Chryso Black", "base_price_rands": 498.35, "stock_quantity": 0 },
        { "code": "SQUTY-MD-AMP", "size": "Medium | 370mm", "color": "Amper", "base_price_rands": 211.14, "stock_quantity": 0 },
        { "code": "SQUTY-MD-FWH", "size": "Medium | 370mm", "color": "Flinted White", "base_price_rands": 211.14, "stock_quantity": 0 },
        { "code": "SQUTY-MD-GRA", "size": "Medium | 370mm", "color": "Granite", "base_price_rands": 211.14, "stock_quantity": 0 },
        { "code": "SQUTY-MD-GRA-2", "size": "Medium | 370mm", "color": "Granite Sealed", "base_price_rands": 211.14, "stock_quantity": 0 },
        { "code": "SQUTY-MD-ROC", "size": "Medium | 370mm", "color": "Rock", "base_price_rands": 211.14, "stock_quantity": 0 },
        { "code": "SQUTY-MD-VEL", "size": "Medium | 370mm", "color": "Velvet", "base_price_rands": 211.14, "stock_quantity": 0 },
        { "code": "SQUTY-MD-CHR", "size": "Medium | 370mm", "color": "Chryso Black", "base_price_rands": 211.14, "stock_quantity": 0 },
        { "code": "SQUTY-SM-AMP", "size": "Small | 300mm", "color": "Amper", "base_price_rands": 167.67, "stock_quantity": 0 },
        { "code": "SQUTY-SM-FWH", "size": "Small | 300mm", "color": "Flinted White", "base_price_rands": 167.67, "stock_quantity": 0 },
        { "code": "SQUTY-SM-GRA", "size": "Small | 300mm", "color": "Granite", "base_price_rands": 167.67, "stock_quantity": 0 },
        { "code": "SQUTY-SM-GRA-2", "size": "Small | 300mm", "color": "Granite Sealed", "base_price_rands": 167.67, "stock_quantity": 0 },
        { "code": "SQUTY-SM-ROC", "size": "Small | 300mm", "color": "Rock", "base_price_rands": 167.67, "stock_quantity": 0 },
        { "code": "SQUTY-SM-VEL", "size": "Small | 300mm", "color": "Velvet", "base_price_rands": 167.67, "stock_quantity": 0 },
        { "code": "SQUTY-SM-CHR", "size": "Small | 300mm", "color": "Chryso Black", "base_price_rands": 167.67, "stock_quantity": 0 },
        { "code": "SQUTY-210-AMP", "size": "Baby | 210mm", "color": "Amper", "base_price_rands": 109.97, "stock_quantity": 0 },
        { "code": "SQUTY-210-FWH", "size": "Baby | 210mm", "color": "Flinted White", "base_price_rands": 109.97, "stock_quantity": 0 },
        { "code": "SQUTY-210-GRA", "size": "Baby | 210mm", "color": "Granite", "base_price_rands": 109.97, "stock_quantity": 0 },
        { "code": "SQUTY-210-GRA-2", "size": "Baby | 210mm", "color": "Granite Sealed", "base_price_rands": 109.97, "stock_quantity": 0 },
        { "code": "SQUTY-210-ROC", "size": "Baby | 210mm", "color": "Rock", "base_price_rands": 109.97, "stock_quantity": 0 },
        { "code": "SQUTY-210-VEL", "size": "Baby | 210mm", "color": "Velvet", "base_price_rands": 109.97, "stock_quantity": 0 },
        { "code": "SQUTY-210-CHR", "size": "Baby | 210mm", "color": "Chryso Black", "base_price_rands": 109.97, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Square Tray (Legs)",
      "category": "Concrete Tray",
      "description_html": "",
      "skus": [
        { "code": "SQUTYLEG-LG-AMP", "size": "Large | 370mm", "color": "Amper", "base_price_rands": 498.35, "stock_quantity": 0 },
        { "code": "SQUTYLEG-LG-FWH", "size": "Large | 370mm", "color": "Flinted White", "base_price_rands": 498.35, "stock_quantity": 0 },
        { "code": "SQUTYLEG-LG-GRA", "size": "Large | 370mm", "color": "Granite", "base_price_rands": 498.35, "stock_quantity": 0 },
        { "code": "SQUTYLEG-LG-GRA-2", "size": "Large | 370mm", "color": "Granite Sealed", "base_price_rands": 498.35, "stock_quantity": 0 },
        { "code": "SQUTYLEG-LG-ROC", "size": "Large | 370mm", "color": "Rock", "base_price_rands": 498.35, "stock_quantity": 0 },
        { "code": "SQUTYLEG-LG-VEL", "size": "Large | 370mm", "color": "Velvet", "base_price_rands": 498.35, "stock_quantity": 0 },
        { "code": "SQUTYLEG-LG-CHR", "size": "Large | 370mm", "color": "Chryso Black", "base_price_rands": 498.35, "stock_quantity": 0 },
        { "code": "SQUTYLEG-MD-AMP", "size": "Medium | 260mm", "color": "Amper", "base_price_rands": 284.38, "stock_quantity": 0 },
        { "code": "SQUTYLEG-MD-FWH", "size": "Medium | 260mm", "color": "Flinted White", "base_price_rands": 284.38, "stock_quantity": 0 },
        { "code": "SQUTYLEG-MD-GRA", "size": "Medium | 260mm", "color": "Granite", "base_price_rands": 284.38, "stock_quantity": 0 },
        { "code": "SQUTYLEG-MD-GRA-2", "size": "Medium | 260mm", "color": "Granite Sealed", "base_price_rands": 284.38, "stock_quantity": 0 },
        { "code": "SQUTYLEG-MD-ROC", "size": "Medium | 260mm", "color": "Rock", "base_price_rands": 284.38, "stock_quantity": 0 },
        { "code": "SQUTYLEG-MD-VEL", "size": "Medium | 260mm", "color": "Velvet", "base_price_rands": 284.38, "stock_quantity": 0 },
        { "code": "SQUTYLEG-MD-CHR", "size": "Medium | 260mm", "color": "Chryso Black", "base_price_rands": 284.38, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Round Tray",
      "category": "Concrete Tray",
      "description_html": "",
      "skus": [
        { "code": "ROUTY-MD-AMP", "size": "Medium | 630mm", "color": "Amper", "base_price_rands": 626.04, "stock_quantity": 0 },
        { "code": "ROUTY-MD-FWH", "size": "Medium | 630mm", "color": "Flinted White", "base_price_rands": 626.04, "stock_quantity": 0 },
        { "code": "ROUTY-MD-GRA", "size": "Medium | 630mm", "color": "Granite", "base_price_rands": 626.04, "stock_quantity": 0 },
        { "code": "ROUTY-MD-GRA-2", "size": "Medium | 630mm", "color": "Granite Sealed", "base_price_rands": 626.04, "stock_quantity": 0 },
        { "code": "ROUTY-MD-ROC", "size": "Medium | 630mm", "color": "Rock", "base_price_rands": 626.04, "stock_quantity": 0 },
        { "code": "ROUTY-MD-VEL", "size": "Medium | 630mm", "color": "Velvet", "base_price_rands": 626.04, "stock_quantity": 0 },
        { "code": "ROUTY-MD-CHR", "size": "Medium | 630mm", "color": "Chryso Black", "base_price_rands": 626.04, "stock_quantity": 0 },
        { "code": "ROUTY-SM-AMP", "size": "Small | 440mm", "color": "Amper", "base_price_rands": 451.19, "stock_quantity": 0 },
        { "code": "ROUTY-SM-FWH", "size": "Small | 440mm", "color": "Flinted White", "base_price_rands": 451.19, "stock_quantity": 0 },
        { "code": "ROUTY-SM-GRA", "size": "Small | 440mm", "color": "Granite", "base_price_rands": 451.19, "stock_quantity": 0 },
        { "code": "ROUTY-SM-GRA-2", "size": "Small | 440mm", "color": "Granite Sealed", "base_price_rands": 451.19, "stock_quantity": 0 },
        { "code": "ROUTY-SM-ROC", "size": "Small | 440mm", "color": "Rock", "base_price_rands": 451.19, "stock_quantity": 0 },
        { "code": "ROUTY-SM-VEL", "size": "Small | 440mm", "color": "Velvet", "base_price_rands": 451.19, "stock_quantity": 0 },
        { "code": "ROUTY-SM-CHR", "size": "Small | 440mm", "color": "Chryso Black", "base_price_rands": 451.19, "stock_quantity": 0 },
        { "code": "ROUTY-350-AMP", "size": "Tiny | 350mm", "color": "Amper", "base_price_rands": 315.84, "stock_quantity": 0 },
        { "code": "ROUTY-350-FWH", "size": "Tiny | 350mm", "color": "Flinted White", "base_price_rands": 315.84, "stock_quantity": 0 },
        { "code": "ROUTY-350-GRA", "size": "Tiny | 350mm", "color": "Granite", "base_price_rands": 315.84, "stock_quantity": 0 },
        { "code": "ROUTY-350-GRA-2", "size": "Tiny | 350mm", "color": "Granite Sealed", "base_price_rands": 315.84, "stock_quantity": 0 },
        { "code": "ROUTY-350-ROC", "size": "Tiny | 350mm", "color": "Rock", "base_price_rands": 315.84, "stock_quantity": 0 },
        { "code": "ROUTY-350-VEL", "size": "Tiny | 350mm", "color": "Velvet", "base_price_rands": 315.84, "stock_quantity": 0 },
        { "code": "ROUTY-350-CHR", "size": "Tiny | 350mm", "color": "Chryso Black", "base_price_rands": 315.84, "stock_quantity": 0 },
        { "code": "ROUTY-225-AMP", "size": "Baby | 225mm", "color": "Amper", "base_price_rands": 169.19, "stock_quantity": 0 },
        { "code": "ROUTY-225-FWH", "size": "Baby | 225mm", "color": "Flinted White", "base_price_rands": 169.19, "stock_quantity": 0 },
        { "code": "ROUTY-225-GRA", "size": "Baby | 225mm", "color": "Granite", "base_price_rands": 169.19, "stock_quantity": 0 },
        { "code": "ROUTY-225-GRA-2", "size": "Baby | 225mm", "color": "Granite Sealed", "base_price_rands": 169.19, "stock_quantity": 0 },
        { "code": "ROUTY-225-ROC", "size": "Baby | 225mm", "color": "Rock", "base_price_rands": 169.19, "stock_quantity": 0 },
        { "code": "ROUTY-225-VEL", "size": "Baby | 225mm", "color": "Velvet", "base_price_rands": 169.19, "stock_quantity": 0 },
        { "code": "ROUTY-225-CHR", "size": "Baby | 225mm", "color": "Chryso Black", "base_price_rands": 169.19, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Curvy Trough Tray",
      "category": "Concrete Tray",
      "description_html": "",
      "skus": [
        { "code": "CURTRTY-LG-AMP-2", "size": "Large | 1000mm x 330mm", "color": "Amper", "base_price_rands": 357.86, "stock_quantity": 0 },
        { "code": "CURTRTY-LG-FWH-2", "size": "Large | 1000mm x 330mm", "color": "Flinted White", "base_price_rands": 357.86, "stock_quantity": 0 },
        { "code": "CURTRTY-LG-GRA-3", "size": "Large | 1000mm x 330mm", "color": "Granite", "base_price_rands": 357.86, "stock_quantity": 0 },
        { "code": "CURTRTY-LG-GRA-4", "size": "Large | 1000mm x 330mm", "color": "Granite Sealed", "base_price_rands": 357.86, "stock_quantity": 0 },
        { "code": "CURTRTY-LG-ROC-2", "size": "Large | 1000mm x 330mm", "color": "Rock", "base_price_rands": 357.86, "stock_quantity": 0 },
        { "code": "CURTRTY-LG-VEL-2", "size": "Large | 1000mm x 330mm", "color": "Velvet", "base_price_rands": 357.86, "stock_quantity": 0 },
        { "code": "CURTRTY-LG-CHR-2", "size": "Large | 1000mm x 330mm", "color": "Chryso Black", "base_price_rands": 357.86, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Chunky Trough Tray",
      "category": "Concrete Tray",
      "description_html": "",
      "skus": [
        { "code": "CHUTRTY-LG-AMP", "size": "Large | 990mm x 480mm", "color": "Amper", "base_price_rands": 629.12, "stock_quantity": 0 },
        { "code": "CHUTRTY-LG-FWH", "size": "Large | 990mm x 480mm", "color": "Flinted White", "base_price_rands": 629.12, "stock_quantity": 0 },
        { "code": "CHUTRTY-LG-GRA", "size": "Large | 990mm x 480mm", "color": "Granite", "base_price_rands": 629.12, "stock_quantity": 0 },
        { "code": "CHUTRTY-LG-GRA-2", "size": "Large | 990mm x 480mm", "color": "Granite Sealed", "base_price_rands": 629.12, "stock_quantity": 0 },
        { "code": "CHUTRTY-LG-ROC", "size": "Large | 990mm x 480mm", "color": "Rock", "base_price_rands": 629.12, "stock_quantity": 0 },
        { "code": "CHUTRTY-LG-VEL", "size": "Large | 990mm x 480mm", "color": "Velvet", "base_price_rands": 629.12, "stock_quantity": 0 },
        { "code": "CHUTRTY-LG-CHR", "size": "Large | 990mm x 480mm", "color": "Chryso Black", "base_price_rands": 629.12, "stock_quantity": 0 },
        { "code": "CHUTRTY-MD-AMP", "size": "Medium | 790mm x 430mm", "color": "Amper", "base_price_rands": 507.35, "stock_quantity": 0 },
        { "code": "CHUTRTY-MD-FWH", "size": "Medium | 790mm x 430mm", "color": "Flinted White", "base_price_rands": 507.35, "stock_quantity": 0 },
        { "code": "CHUTRTY-MD-GRA", "size": "Medium | 790mm x 430mm", "color": "Granite", "base_price_rands": 507.35, "stock_quantity": 0 },
        { "code": "CHUTRTY-MD-GRA-2", "size": "Medium | 790mm x 430mm", "color": "Granite Sealed", "base_price_rands": 507.35, "stock_quantity": 0 },
        { "code": "CHUTRTY-MD-ROC", "size": "Medium | 790mm x 430mm", "color": "Rock", "base_price_rands": 507.35, "stock_quantity": 0 },
        { "code": "CHUTRTY-MD-VEL", "size": "Medium | 790mm x 430mm", "color": "Velvet", "base_price_rands": 507.35, "stock_quantity": 0 },
        { "code": "CHUTRTY-MD-CHR", "size": "Medium | 790mm x 430mm", "color": "Chryso Black", "base_price_rands": 507.35, "stock_quantity": 0 },
        { "code": "CHUTRTY-SM-AMP", "size": "Small | 640mm x 380mm", "color": "Amper", "base_price_rands": 475.88, "stock_quantity": 0 },
        { "code": "CHUTRTY-SM-FWH", "size": "Small | 640mm x 380mm", "color": "Flinted White", "base_price_rands": 475.88, "stock_quantity": 0 },
        { "code": "CHUTRTY-SM-GRA", "size": "Small | 640mm x 380mm", "color": "Granite", "base_price_rands": 475.88, "stock_quantity": 0 },
        { "code": "CHUTRTY-SM-GRA-2", "size": "Small | 640mm x 380mm", "color": "Granite Sealed", "base_price_rands": 475.88, "stock_quantity": 0 },
        { "code": "CHUTRTY-SM-ROC", "size": "Small | 640mm x 380mm", "color": "Rock", "base_price_rands": 475.88, "stock_quantity": 0 },
        { "code": "CHUTRTY-SM-VEL", "size": "Small | 640mm x 380mm", "color": "Velvet", "base_price_rands": 475.88, "stock_quantity": 0 },
        { "code": "CHUTRTY-SM-CHR", "size": "Small | 640mm x 380mm", "color": "Chryso Black", "base_price_rands": 475.88, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Skinny Trough Tray",
      "category": "Concrete Tray",
      "description_html": "",
      "skus": [
        { "code": "SKITRTY-LG-AMP", "size": "Large | 1000mm x 290mm", "color": "Amper", "base_price_rands": 405.88, "stock_quantity": 0 },
        { "code": "SKITRTY-LG-FWH", "size": "Large | 1000mm x 290mm", "color": "Flinted White", "base_price_rands": 405.88, "stock_quantity": 0 },
        { "code": "SKITRTY-LG-GRA", "size": "Large | 1000mm x 290mm", "color": "Granite", "base_price_rands": 405.88, "stock_quantity": 0 },
        { "code": "SKITRTY-LG-GRA-2", "size": "Large | 1000mm x 290mm", "color": "Granite Sealed", "base_price_rands": 405.88, "stock_quantity": 0 },
        { "code": "SKITRTY-LG-ROC", "size": "Large | 1000mm x 290mm", "color": "Rock", "base_price_rands": 405.88, "stock_quantity": 0 },
        { "code": "SKITRTY-LG-VEL", "size": "Large | 1000mm x 290mm", "color": "Velvet", "base_price_rands": 405.88, "stock_quantity": 0 },
        { "code": "SKITRTY-LG-CHR", "size": "Large | 1000mm x 290mm", "color": "Chryso Black", "base_price_rands": 405.88, "stock_quantity": 0 },
        { "code": "SKITRTY-SM-AMP", "size": "Small | 600mm x 290mm", "color": "Amper", "base_price_rands": 251.66, "stock_quantity": 0 },
        { "code": "SKITRTY-SM-FWH", "size": "Small | 600mm x 290mm", "color": "Flinted White", "base_price_rands": 251.66, "stock_quantity": 0 },
        { "code": "SKITRTY-SM-GRA", "size": "Small | 600mm x 290mm", "color": "Granite", "base_price_rands": 251.66, "stock_quantity": 0 },
        { "code": "SKITRTY-SM-GRA-2", "size": "Small | 600mm x 290mm", "color": "Granite Sealed", "base_price_rands": 251.66, "stock_quantity": 0 },
        { "code": "SKITRTY-SM-ROC", "size": "Small | 600mm x 290mm", "color": "Rock", "base_price_rands": 251.66, "stock_quantity": 0 },
        { "code": "SKITRTY-SM-VEL", "size": "Small | 600mm x 290mm", "color": "Velvet", "base_price_rands": 251.66, "stock_quantity": 0 },
        { "code": "SKITRTY-SM-CHR", "size": "Small | 600mm x 290mm", "color": "Chryso Black", "base_price_rands": 405.88, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Retro Slim Square Pond",
      "category": "Pond",
      "description_html": "",
      "skus": [
        { "code": "RETSLISQUPON-LG-AMP", "size": "Large | 720mm x 200mm", "color": "Amper", "base_price_rands": 2416.2, "stock_quantity": 0 },
        { "code": "RETSLISQUPON-LG-FWH", "size": "Large | 720mm x 200mm", "color": "Flinted White", "base_price_rands": 2416.2, "stock_quantity": 0 },
        { "code": "RETSLISQUPON-LG-GRA", "size": "Large | 720mm x 200mm", "color": "Granite", "base_price_rands": 2416.2, "stock_quantity": 0 },
        { "code": "RETSLISQUPON-LG-GRA-2", "size": "Large | 720mm x 200mm", "color": "Granite light Sealed", "base_price_rands": 2416.2, "stock_quantity": 0 },
        { "code": "RETSLISQUPON-LG-ROC", "size": "Large | 720mm x 200mm", "color": "Rock", "base_price_rands": 2416.2, "stock_quantity": 0 },
        { "code": "RETSLISQUPON-LG-VEL", "size": "Large | 720mm x 200mm", "color": "Velvet", "base_price_rands": 2416.2, "stock_quantity": 0 },
        { "code": "RETSLISQUPON-LG-CHR", "size": "Large | 720mm x 200mm", "color": "Chryso Black", "base_price_rands": 2416.2, "stock_quantity": 0 },
        { "code": "RETSLISQUPON-LG-CHA", "size": "Large | 720mm x 200mm", "color": "charcoal light", "base_price_rands": 2416.2, "stock_quantity": 0 },
        { "code": "RETSLISQUPON-LG-CHA-2", "size": "Large | 720mm x 200mm", "color": "charcoal dark", "base_price_rands": 2416.2, "stock_quantity": 0 },
        { "code": "RETSLISQUPON-LG-GRA-3", "size": "Large | 720mm x 200mm", "color": "granite dark sealed", "base_price_rands": 2416.2, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Texan Trough",
      "category": "Concrete Pots",
      "description_html": "",
      "skus": [
        { "code": "TEXTRO-LG-AMP", "size": "Large | 600mm x 90mm", "color": "Amper", "base_price_rands": 1019.81, "stock_quantity": 0 },
        { "code": "TEXTRO-LG-FWH", "size": "Large | 600mm x 90mm", "color": "Flinted White", "base_price_rands": 1019.81, "stock_quantity": 0 },
        { "code": "TEXTRO-LG-GRA", "size": "Large | 600mm x 90mm", "color": "Granite", "base_price_rands": 1019.81, "stock_quantity": 0 },
        { "code": "TEXTRO-LG-GRA-2", "size": "Large | 600mm x 90mm", "color": "Granite Sealed", "base_price_rands": 1019.81, "stock_quantity": 0 },
        { "code": "TEXTRO-LG-ROC", "size": "Large | 600mm x 90mm", "color": "Rock", "base_price_rands": 1019.81, "stock_quantity": 0 },
        { "code": "TEXTRO-LG-VEL", "size": "Large | 600mm x 90mm", "color": "Velvet", "base_price_rands": 1019.81, "stock_quantity": 0 },
        { "code": "TEXTRO-LG-CHR", "size": "Large | 600mm x 90mm", "color": "Chryso Black", "base_price_rands": 1019.81, "stock_quantity": 0 },
        { "code": "TEXTRO-MD-AMP", "size": "Medium | 500mm x 90mm", "color": "Amper", "base_price_rands": 809.84, "stock_quantity": 0 },
        { "code": "TEXTRO-MD-FWH", "size": "Medium | 500mm x 90mm", "color": "Flinted White", "base_price_rands": 809.84, "stock_quantity": 0 },
        { "code": "TEXTRO-MD-GRA", "size": "Medium | 500mm x 90mm", "color": "Granite", "base_price_rands": 809.84, "stock_quantity": 0 },
        { "code": "TEXTRO-MD-GRA-2", "size": "Medium | 500mm x 90mm", "color": "Granite Sealed", "base_price_rands": 809.84, "stock_quantity": 0 },
        { "code": "TEXTRO-MD-ROC", "size": "Medium | 500mm x 90mm", "color": "Rock", "base_price_rands": 809.84, "stock_quantity": 0 },
        { "code": "TEXTRO-MD-VEL", "size": "Medium | 500mm x 90mm", "color": "Velvet", "base_price_rands": 809.84, "stock_quantity": 0 },
        { "code": "TEXTRO-MD-CHR", "size": "Medium | 500mm x 90mm", "color": "Chryso Black", "base_price_rands": 809.84, "stock_quantity": 0 },
        { "code": "TEXTRO-SM-AMP", "size": "Small | 400mm x 90mm", "color": "Amper", "base_price_rands": 349.92, "stock_quantity": 0 },
        { "code": "TEXTRO-SM-FWH", "size": "Small | 400mm x 90mm", "color": "Flinted White", "base_price_rands": 349.92, "stock_quantity": 0 },
        { "code": "TEXTRO-SM-GRA", "size": "Small | 400mm x 90mm", "color": "Granite", "base_price_rands": 349.92, "stock_quantity": 0 },
        { "code": "TEXTRO-SM-GRA-2", "size": "Small | 400mm x 90mm", "color": "Granite Sealed", "base_price_rands": 349.92, "stock_quantity": 0 },
        { "code": "TEXTRO-SM-ROC", "size": "Small | 400mm x 90mm", "color": "Rock", "base_price_rands": 349.92, "stock_quantity": 0 },
        { "code": "TEXTRO-SM-VEL", "size": "Small | 400mm x 90mm", "color": "Velvet", "base_price_rands": 349.92, "stock_quantity": 0 },
        { "code": "TEXTRO-SM-CHR", "size": "Small | 400mm x 90mm", "color": "Chryso Black", "base_price_rands": 349.92, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Square Pillar Pond",
      "category": "Pond",
      "description_html": "",
      "skus": [
        { "code": "SQUPILPON-LG-AMP", "size": "Large | 870mm x 260mm", "color": "amper", "base_price_rands": 2241.12, "stock_quantity": 0 },
        { "code": "SQUPILPON-LG-GRD", "size": "Large | 870mm x 260mm", "color": "granite dark", "base_price_rands": 2241.12, "stock_quantity": 0 },
        { "code": "SQUPILPON-LG-BRO", "size": "Large | 870mm x 260mm", "color": "bronze", "base_price_rands": 2241.12, "stock_quantity": 0 },
        { "code": "SQUPILPON-LG-CHR", "size": "Large | 870mm x 260mm", "color": "charcoal", "base_price_rands": 2241.12, "stock_quantity": 0 },
        { "code": "SQUPILPON-LG-CHR-2", "size": "Large | 870mm x 260mm", "color": "chryso black", "base_price_rands": 2241.12, "stock_quantity": 0 },
        { "code": "SQUPILPON-LG-GRL", "size": "Large | 870mm x 260mm", "color": "granite light", "base_price_rands": 2241.12, "stock_quantity": 0 },
        { "code": "SQUPILPON-LG-ROC", "size": "Large | 870mm x 260mm", "color": "rock", "base_price_rands": 2241.12, "stock_quantity": 0 },
        { "code": "SQUPILPON-LG-VEL", "size": "Large | 870mm x 260mm", "color": "velvet", "base_price_rands": 2241.12, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Succulent Planter",
      "category": "Concrete Pots",
      "description_html": "",
      "skus": [
        { "code": "SUCPLA-LG-AMP", "size": "Large | 550mm x 135mm", "color": "amper", "base_price_rands": 295.0, "stock_quantity": 0 },
        { "code": "SUCPLA-LG-ANT", "size": "Large | 550mm x 135mm", "color": "antique rust", "base_price_rands": 295.0, "stock_quantity": 0 },
        { "code": "SUCPLA-LG-BRO", "size": "Large | 550mm x 135mm", "color": "bronze", "base_price_rands": 295.0, "stock_quantity": 0 },
        { "code": "SUCPLA-LG-CHR", "size": "Large | 550mm x 135mm", "color": "charcoal", "base_price_rands": 295.0, "stock_quantity": 0 },
        { "code": "SUCPLA-LG-CHR-2", "size": "Large | 550mm x 135mm", "color": "chryso black", "base_price_rands": 295.0, "stock_quantity": 0 },
        { "code": "SUCPLA-LG-GRA", "size": "Large | 550mm x 135mm", "color": "granite", "base_price_rands": 295.0, "stock_quantity": 0 },
        { "code": "SUCPLA-LG-ROC", "size": "Large | 550mm x 135mm", "color": "rock", "base_price_rands": 295.0, "stock_quantity": 0 },
        { "code": "SUCPLA-LG-VEL", "size": "Large | 550mm x 135mm", "color": "velvet", "base_price_rands": 295.0, "stock_quantity": 0 },
        { "code": "SUCPLA-LG-RAW", "size": "Large | 550mm x 135mm", "color": "raw", "base_price_rands": 295.0, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Regency Trough",
      "category": "Concrete Pots",
      "description_html": "",
      "skus": [
        { "code": "REGTRO-LG-AMP", "size": "Large | 270mm x 330mm x 1260mm", "color": "amper", "base_price_rands": 1179.76, "stock_quantity": 0 },
        { "code": "REGTRO-LG-ANT", "size": "Large | 270mm x 330mm x 1260mm", "color": "antique rust", "base_price_rands": 1179.76, "stock_quantity": 0 },
        { "code": "REGTRO-LG-BRO", "size": "Large | 270mm x 330mm x 1260mm", "color": "bronze", "base_price_rands": 1179.76, "stock_quantity": 0 },
        { "code": "REGTRO-LG-CHR", "size": "Large | 270mm x 330mm x 1260mm", "color": "charcoal", "base_price_rands": 1179.76, "stock_quantity": 0 },
        { "code": "REGTRO-LG-CHR-2", "size": "Large | 270mm x 330mm x 1260mm", "color": "chryso black", "base_price_rands": 1179.76, "stock_quantity": 0 },
        { "code": "REGTRO-LG-GRA", "size": "Large | 270mm x 330mm x 1260mm", "color": "granite", "base_price_rands": 1179.76, "stock_quantity": 0 },
        { "code": "REGTRO-LG-ROC", "size": "Large | 270mm x 330mm x 1260mm", "color": "rock", "base_price_rands": 1179.76, "stock_quantity": 0 },
        { "code": "REGTRO-LG-VEL", "size": "Large | 270mm x 330mm x 1260mm", "color": "velvet", "base_price_rands": 1179.76, "stock_quantity": 0 },
        { "code": "REGTRO-LG-RAW", "size": "Large | 270mm x 330mm x 1260mm", "color": "raw", "base_price_rands": 1179.76, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Skinny Trough",
      "category": "Concrete Pots",
      "description_html": "",
      "skus": [
        { "code": "SKITRO-LG-AMP", "size": "Large | 210mm x 230mm x 980mm", "color": "Amper", "base_price_rands": 679.54, "stock_quantity": 0 },
        { "code": "SKITRO-LG-FWH", "size": "Large | 210mm x 230mm x 980mm", "color": "Flinted White", "base_price_rands": 679.54, "stock_quantity": 0 },
        { "code": "SKITRO-LG-GRA", "size": "Large | 210mm x 230mm x 980mm", "color": "Granite", "base_price_rands": 679.54, "stock_quantity": 0 },
        { "code": "SKITRO-LG-GRA-2", "size": "Large | 210mm x 230mm x 980mm", "color": "Granite Sealed", "base_price_rands": 679.54, "stock_quantity": 0 },
        { "code": "SKITRO-LG-ROC", "size": "Large | 210mm x 230mm x 980mm", "color": "Rock", "base_price_rands": 679.54, "stock_quantity": 0 },
        { "code": "SKITRO-LG-VEL", "size": "Large | 210mm x 230mm x 980mm", "color": "Velvet", "base_price_rands": 679.54, "stock_quantity": 0 },
        { "code": "SKITRO-LG-CHR", "size": "Large | 210mm x 230mm x 980mm", "color": "Chryso Black", "base_price_rands": 679.54, "stock_quantity": 0 },
        { "code": "SKITRO-SM-AMP", "size": "Small | 210mm x 230mm x 560mm", "color": "Amper", "base_price_rands": 454.08, "stock_quantity": 0 },
        { "code": "SKITRO-SM-FWH", "size": "Small | 210mm x 230mm x 560mm", "color": "Flinted White", "base_price_rands": 454.08, "stock_quantity": 0 },
        { "code": "SKITRO-SM-GRA", "size": "Small | 210mm x 230mm x 560mm", "color": "Granite", "base_price_rands": 454.08, "stock_quantity": 0 },
        { "code": "SKITRO-SM-GRA-2", "size": "Small | 210mm x 230mm x 560mm", "color": "Granite Sealed", "base_price_rands": 454.08, "stock_quantity": 0 },
        { "code": "SKITRO-SM-ROC", "size": "Small | 210mm x 230mm x 560mm", "color": "Rock", "base_price_rands": 454.08, "stock_quantity": 0 },
        { "code": "SKITRO-SM-VEL", "size": "Small | 210mm x 230mm x 560mm", "color": "Velvet", "base_price_rands": 454.08, "stock_quantity": 0 },
        { "code": "SKITRO-SM-CHR", "size": "Small | 210mm x 230mm x 560mm", "color": "Chryso Black", "base_price_rands": 679.54, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Tulip Lip Trough",
      "category": "Concrete Pots",
      "description_html": "",
      "skus": [
        { "code": "TULLIPTRO-LG-AMP", "size": "Large | 500mm x 365mm x 750mm", "color": "Amper", "base_price_rands": 1403.06, "stock_quantity": 0 },
        { "code": "TULLIPTRO-LG-FWH", "size": "Large | 500mm x 365mm x 750mm", "color": "Flinted White", "base_price_rands": 1403.06, "stock_quantity": 0 },
        { "code": "TULLIPTRO-LG-GRA", "size": "Large | 500mm x 365mm x 750mm", "color": "Granite", "base_price_rands": 1403.06, "stock_quantity": 0 },
        { "code": "TULLIPTRO-LG-GRA-2", "size": "Large | 500mm x 365mm x 750mm", "color": "Granite Sealed", "base_price_rands": 1403.06, "stock_quantity": 0 },
        { "code": "TULLIPTRO-LG-ROC", "size": "Large | 500mm x 365mm x 750mm", "color": "Rock", "base_price_rands": 1403.06, "stock_quantity": 0 },
        { "code": "TULLIPTRO-LG-VEL", "size": "Large | 500mm x 365mm x 750mm", "color": "Velvet", "base_price_rands": 1403.06, "stock_quantity": 0 },
        { "code": "TULLIPTRO-LG-CHR", "size": "Large | 500mm x 365mm x 750mm", "color": "Chryso Black", "base_price_rands": 1403.06, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Tulip Trough",
      "category": "Concrete Pots",
      "description_html": "",
      "skus": [
        { "code": "TULTRO-LG-AMP", "size": "Large | 500mm x 320mm x 710mm", "color": "Amper", "base_price_rands": 1323.09, "stock_quantity": 0 },
        { "code": "TULTRO-LG-FWH", "size": "Large | 500mm x 320mm x 710mm", "color": "Flinted White", "base_price_rands": 1323.09, "stock_quantity": 0 },
        { "code": "TULTRO-LG-GRA", "size": "Large | 500mm x 320mm x 710mm", "color": "Granite", "base_price_rands": 1323.09, "stock_quantity": 0 },
        { "code": "TULTRO-LG-GRA-2", "size": "Large | 500mm x 320mm x 710mm", "color": "Granite Sealed", "base_price_rands": 1323.09, "stock_quantity": 0 },
        { "code": "TULTRO-LG-ROC", "size": "Large | 500mm x 320mm x 710mm", "color": "Rock", "base_price_rands": 1323.09, "stock_quantity": 0 },
        { "code": "TULTRO-LG-VEL", "size": "Large | 500mm x 320mm x 710mm", "color": "Velvet", "base_price_rands": 1323.09, "stock_quantity": 0 },
        { "code": "TULTRO-LG-CHR", "size": "Large | 500mm x 320mm x 710mm", "color": "Chryso Black", "base_price_rands": 1323.09, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Retro Trough",
      "category": "Concrete Pots",
      "description_html": "",
      "skus": [
        { "code": "RETTRO-LG-AMP", "size": "Large | 730mm x 330mm x 930mm", "color": "amper", "base_price_rands": 2568.3, "stock_quantity": 0 },
        { "code": "RETTRO-LG-ANT", "size": "Large | 730mm x 330mm x 930mm", "color": "antique rust", "base_price_rands": 2568.3, "stock_quantity": 0 },
        { "code": "RETTRO-LG-BRO", "size": "Large | 730mm x 330mm x 930mm", "color": "bronze", "base_price_rands": 2568.3, "stock_quantity": 0 },
        { "code": "RETTRO-LG-CHR", "size": "Large | 730mm x 330mm x 930mm", "color": "charcoal", "base_price_rands": 2568.3, "stock_quantity": 0 },
        { "code": "RETTRO-LG-CHR-2", "size": "Large | 730mm x 330mm x 930mm", "color": "chryso black", "base_price_rands": 2568.3, "stock_quantity": 0 },
        { "code": "RETTRO-LG-GRA", "size": "Large | 730mm x 330mm x 930mm", "color": "granite", "base_price_rands": 2568.3, "stock_quantity": 0 },
        { "code": "RETTRO-LG-ROC", "size": "Large | 730mm x 330mm x 930mm", "color": "rock", "base_price_rands": 2568.3, "stock_quantity": 0 },
        { "code": "RETTRO-LG-VEL", "size": "Large | 730mm x 330mm x 930mm", "color": "velvet", "base_price_rands": 2568.3, "stock_quantity": 0 },
        { "code": "RETTRO-LG-RAW", "size": "Large | 730mm x 330mm x 930mm", "color": "raw", "base_price_rands": 2568.3, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Pongola Concrete Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "PONCPOT-890-AMP", "size": "890mm x 580mm", "color": "amper", "base_price_rands": 2602.29, "stock_quantity": 0 },
        { "code": "PONCPOT-890-ANT", "size": "890mm x 580mm", "color": "antique rust", "base_price_rands": 2602.29, "stock_quantity": 0 },
        { "code": "PONCPOT-890-BRO", "size": "890mm x 580mm", "color": "bronze", "base_price_rands": 2602.29, "stock_quantity": 0 },
        { "code": "PONCPOT-890-CHR", "size": "890mm x 580mm", "color": "charcoal", "base_price_rands": 2602.29, "stock_quantity": 0 },
        { "code": "PONCPOT-890-CHR-2", "size": "890mm x 580mm", "color": "chryso black", "base_price_rands": 2602.29, "stock_quantity": 0 },
        { "code": "PONCPOT-890-GRA", "size": "890mm x 580mm", "color": "granite", "base_price_rands": 2602.29, "stock_quantity": 0 },
        { "code": "PONCPOT-890-ROC", "size": "890mm x 580mm", "color": "rock", "base_price_rands": 2602.29, "stock_quantity": 0 },
        { "code": "PONCPOT-890-VEL", "size": "890mm x 580mm", "color": "velvet", "base_price_rands": 2602.29, "stock_quantity": 0 },
        { "code": "PONCPOT-890-RAW", "size": "890mm x 580mm", "color": "raw", "base_price_rands": 2602.29, "stock_quantity": 0 },
        { "code": "PONCPOT-890-FWH", "size": "890mm x 580mm", "color": "Flinted white", "base_price_rands": 2602.29, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Plantation Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "PLACPOT-LG-AMP", "size": "Large | 730mm x 525mm", "color": "Amper", "base_price_rands": 2647.3, "stock_quantity": 0 },
        { "code": "PLACPOT-LG-FWH", "size": "Large | 730mm x 525mm", "color": "Flinted White", "base_price_rands": 2647.3, "stock_quantity": 0 },
        { "code": "PLACPOT-LG-GRA", "size": "Large | 730mm x 525mm", "color": "Granite", "base_price_rands": 2647.3, "stock_quantity": 0 },
        { "code": "PLACPOT-LG-GRA-2", "size": "Large | 730mm x 525mm", "color": "Granite Sealed", "base_price_rands": 2647.3, "stock_quantity": 0 },
        { "code": "PLACPOT-LG-ROC", "size": "Large | 730mm x 525mm", "color": "Rock", "base_price_rands": 2647.3, "stock_quantity": 0 },
        { "code": "PLACPOT-LG-VEL", "size": "Large | 730mm x 525mm", "color": "Velvet", "base_price_rands": 2647.3, "stock_quantity": 0 },
        { "code": "PLACPOT-LG-CHR", "size": "Large | 730mm x 525mm", "color": "Chryso Black", "base_price_rands": 2647.3, "stock_quantity": 0 },
        { "code": "PLACPOT-MD-AMP", "size": "Medium | 620mm x 445mm", "color": "Amper", "base_price_rands": 1206.42, "stock_quantity": 0 },
        { "code": "PLACPOT-MD-FWH", "size": "Medium | 620mm x 445mm", "color": "Flinted White", "base_price_rands": 1206.42, "stock_quantity": 0 },
        { "code": "PLACPOT-MD-GRA", "size": "Medium | 620mm x 445mm", "color": "Granite", "base_price_rands": 1206.42, "stock_quantity": 0 },
        { "code": "PLACPOT-MD-GRA-2", "size": "Medium | 620mm x 445mm", "color": "Granite Sealed", "base_price_rands": 1206.42, "stock_quantity": 0 },
        { "code": "PLACPOT-MD-ROC", "size": "Medium | 620mm x 445mm", "color": "Rock", "base_price_rands": 1206.42, "stock_quantity": 0 },
        { "code": "PLACPOT-MD-VEL", "size": "Medium | 620mm x 445mm", "color": "Velvet", "base_price_rands": 1206.42, "stock_quantity": 0 },
        { "code": "PLACPOT-MD-CHR", "size": "Medium | 620mm x 445mm", "color": "Chryso Black", "base_price_rands": 1206.42, "stock_quantity": 0 },
        { "code": "PLACPOT-SM-AMP", "size": "Small | 505mm x 370mm", "color": "Amper", "base_price_rands": 823.18, "stock_quantity": 0 },
        { "code": "PLACPOT-SM-FWH", "size": "Small | 505mm x 370mm", "color": "Flinted White", "base_price_rands": 823.18, "stock_quantity": 0 },
        { "code": "PLACPOT-SM-GRA", "size": "Small | 505mm x 370mm", "color": "Granite", "base_price_rands": 823.18, "stock_quantity": 0 },
        { "code": "PLACPOT-SM-GRA-2", "size": "Small | 505mm x 370mm", "color": "Granite Sealed", "base_price_rands": 823.18, "stock_quantity": 0 },
        { "code": "PLACPOT-SM-ROC", "size": "Small | 505mm x 370mm", "color": "Rock", "base_price_rands": 823.18, "stock_quantity": 0 },
        { "code": "PLACPOT-SM-VEL", "size": "Small | 505mm x 370mm", "color": "Velvet", "base_price_rands": 823.18, "stock_quantity": 0 },
        { "code": "PLACPOT-SM-CHR", "size": "Small | 505mm x 370mm", "color": "Chryso Black", "base_price_rands": 823.18, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Pinto Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "PINCPOT-LG-AMP", "size": "Large | 950mm X 400mm", "color": "Amper", "base_price_rands": 2170.15, "stock_quantity": 0 },
        { "code": "PINCPOT-LG-FWH", "size": "Large | 950mm X 400mm", "color": "Flinted White", "base_price_rands": 2170.15, "stock_quantity": 0 },
        { "code": "PINCPOT-LG-GRA", "size": "Large | 950mm X 400mm", "color": "Granite", "base_price_rands": 2170.15, "stock_quantity": 0 },
        { "code": "PINCPOT-LG-GRA-2", "size": "Large | 950mm X 400mm", "color": "Granite Sealed", "base_price_rands": 2170.15, "stock_quantity": 0 },
        { "code": "PINCPOT-LG-ROC", "size": "Large | 950mm X 400mm", "color": "Rock", "base_price_rands": 2170.15, "stock_quantity": 0 },
        { "code": "PINCPOT-LG-VEL", "size": "Large | 950mm X 400mm", "color": "Velvet", "base_price_rands": 2170.15, "stock_quantity": 0 },
        { "code": "PINCPOT-MD-AMP", "size": "Medium | 750mm X 350mm", "color": "Amper", "base_price_rands": 1236.95, "stock_quantity": 0 },
        { "code": "PINCPOT-MD-FWH", "size": "Medium | 750mm X 350mm", "color": "Flinted White", "base_price_rands": 1236.95, "stock_quantity": 0 },
        { "code": "PINCPOT-MD-GRA", "size": "Medium | 750mm X 350mm", "color": "Granite", "base_price_rands": 1236.95, "stock_quantity": 0 },
        { "code": "PINCPOT-MD-GRA-2", "size": "Medium | 750mm X 350mm", "color": "Granite Sealed", "base_price_rands": 1236.95, "stock_quantity": 0 },
        { "code": "PINCPOT-MD-ROC", "size": "Medium | 750mm X 350mm", "color": "Rock", "base_price_rands": 1236.95, "stock_quantity": 0 },
        { "code": "PINCPOT-MD-VEL", "size": "Medium | 750mm X 350mm", "color": "Velvet", "base_price_rands": 1236.95, "stock_quantity": 0 },
        { "code": "PINCPOT-SM-AMP", "size": "Small | 600mm X 300mm", "color": "Amper", "base_price_rands": 829.86, "stock_quantity": 0 },
        { "code": "PINCPOT-SM-FWH", "size": "Small | 600mm X 300mm", "color": "Flinted White", "base_price_rands": 829.86, "stock_quantity": 0 },
        { "code": "PINCPOT-SM-GRA", "size": "Small | 600mm X 300mm", "color": "Granite", "base_price_rands": 829.86, "stock_quantity": 0 },
        { "code": "PINCPOT-SM-GRA-2", "size": "Small | 600mm X 300mm", "color": "Granite Sealed", "base_price_rands": 829.86, "stock_quantity": 0 },
        { "code": "PINCPOT-SM-ROC", "size": "Small | 600mm X 300mm", "color": "Rock", "base_price_rands": 829.86, "stock_quantity": 0 },
        { "code": "PINCPOT-SM-VEL", "size": "Small | 600mm X 300mm", "color": "Velvet", "base_price_rands": 829.86, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Pear Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "PEACPOT-LG-AMP", "size": "Large | 620mm X 610mm", "color": "amper", "base_price_rands": 1513.73, "stock_quantity": 0 },
        { "code": "PEACPOT-LG-ANT", "size": "Large | 620mm X 610mm", "color": "antique rust", "base_price_rands": 1513.73, "stock_quantity": 0 },
        { "code": "PEACPOT-LG-BRO", "size": "Large | 620mm X 610mm", "color": "bronze", "base_price_rands": 1513.73, "stock_quantity": 0 },
        { "code": "PEACPOT-LG-CHR", "size": "Large | 620mm X 610mm", "color": "charcoal", "base_price_rands": 1513.73, "stock_quantity": 0 },
        { "code": "PEACPOT-LG-CHR-2", "size": "Large | 620mm X 610mm", "color": "chryso black", "base_price_rands": 1513.73, "stock_quantity": 0 },
        { "code": "PEACPOT-LG-GRA", "size": "Large | 620mm X 610mm", "color": "granite", "base_price_rands": 1513.73, "stock_quantity": 0 },
        { "code": "PEACPOT-LG-ROC", "size": "Large | 620mm X 610mm", "color": "rock", "base_price_rands": 1513.73, "stock_quantity": 0 },
        { "code": "PEACPOT-LG-VEL", "size": "Large | 620mm X 610mm", "color": "velvet", "base_price_rands": 1513.73, "stock_quantity": 0 },
        { "code": "PEACPOT-LG-RAW", "size": "Large | 620mm X 610mm", "color": "raw", "base_price_rands": 1513.73, "stock_quantity": 0 },
        { "code": "PEACPOT-MD-AMP", "size": "Medium | 460mm X 460mm", "color": "amper", "base_price_rands": 949.97, "stock_quantity": 0 },
        { "code": "PEACPOT-MD-ANT", "size": "Medium | 460mm X 460mm", "color": "antique rust", "base_price_rands": 949.97, "stock_quantity": 0 },
        { "code": "PEACPOT-MD-BRO", "size": "Medium | 460mm X 460mm", "color": "bronze", "base_price_rands": 949.97, "stock_quantity": 0 },
        { "code": "PEACPOT-MD-CHR", "size": "Medium | 460mm X 460mm", "color": "charcoal", "base_price_rands": 949.97, "stock_quantity": 0 },
        { "code": "PEACPOT-MD-CHR-2", "size": "Medium | 460mm X 460mm", "color": "chryso black", "base_price_rands": 949.97, "stock_quantity": 0 },
        { "code": "PEACPOT-MD-GRA", "size": "Medium | 460mm X 460mm", "color": "granite", "base_price_rands": 949.97, "stock_quantity": 0 },
        { "code": "PEACPOT-MD-ROC", "size": "Medium | 460mm X 460mm", "color": "rock", "base_price_rands": 949.97, "stock_quantity": 0 },
        { "code": "PEACPOT-MD-VEL", "size": "Medium | 460mm X 460mm", "color": "velvet", "base_price_rands": 949.97, "stock_quantity": 0 },
        { "code": "PEACPOT-MD-RAW", "size": "Medium | 460mm X 460mm", "color": "raw", "base_price_rands": 949.97, "stock_quantity": 0 },
        { "code": "PEACPOT-SM-AMP", "size": "Small 310mm X 310mm", "color": "amper", "base_price_rands": 446.89, "stock_quantity": 0 },
        { "code": "PEACPOT-SM-ANT", "size": "Small 310mm X 310mm", "color": "antique rust", "base_price_rands": 446.89, "stock_quantity": 0 },
        { "code": "PEACPOT-SM-BRO", "size": "Small 310mm X 310mm", "color": "bronze", "base_price_rands": 446.89, "stock_quantity": 0 },
        { "code": "PEACPOT-SM-CHR", "size": "Small 310mm X 310mm", "color": "charcoal", "base_price_rands": 446.89, "stock_quantity": 0 },
        { "code": "PEACPOT-SM-CHR-2", "size": "Small 310mm X 310mm", "color": "chryso black", "base_price_rands": 446.89, "stock_quantity": 0 },
        { "code": "PEACPOT-SM-GRA", "size": "Small 310mm X 310mm", "color": "granite", "base_price_rands": 446.89, "stock_quantity": 0 },
        { "code": "PEACPOT-SM-ROC", "size": "Small 310mm X 310mm", "color": "rock", "base_price_rands": 446.89, "stock_quantity": 0 },
        { "code": "PEACPOT-SM-VEL", "size": "Small 310mm X 310mm", "color": "velvet", "base_price_rands": 446.89, "stock_quantity": 0 },
        { "code": "PEACPOT-SM-RAW", "size": "Small 310mm X 310mm", "color": "raw", "base_price_rands": 446.89, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Pafuri Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "PAFCPOT-800-AMP", "size": "800mm x 670mm", "color": "amper", "base_price_rands": 2955.95, "stock_quantity": 0 },
        { "code": "PAFCPOT-800-ANT", "size": "800mm x 670mm", "color": "antique rust", "base_price_rands": 2955.95, "stock_quantity": 0 },
        { "code": "PAFCPOT-800-BRO", "size": "800mm x 670mm", "color": "bronze", "base_price_rands": 2955.95, "stock_quantity": 0 },
        { "code": "PAFCPOT-800-CHR", "size": "800mm x 670mm", "color": "charcoal", "base_price_rands": 2955.95, "stock_quantity": 0 },
        { "code": "PAFCPOT-800-CHR-2", "size": "800mm x 670mm", "color": "chryso black", "base_price_rands": 2955.95, "stock_quantity": 0 },
        { "code": "PAFCPOT-800-GRA", "size": "800mm x 670mm", "color": "granite", "base_price_rands": 2955.95, "stock_quantity": 0 },
        { "code": "PAFCPOT-800-ROC", "size": "800mm x 670mm", "color": "rock", "base_price_rands": 2955.95, "stock_quantity": 0 },
        { "code": "PAFCPOT-800-VEL", "size": "800mm x 670mm", "color": "velvet", "base_price_rands": 2955.95, "stock_quantity": 0 },
        { "code": "PAFCPOT-800-RAW", "size": "800mm x 670mm", "color": "raw", "base_price_rands": 2955.95, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Oval Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "OVACPOT-LG-AMP", "size": "Large | 600mm x 700mm", "color": "Amper", "base_price_rands": 2366.22, "stock_quantity": 0 },
        { "code": "OVACPOT-LG-FWH", "size": "Large | 600mm x 700mm", "color": "Flinted White", "base_price_rands": 2366.22, "stock_quantity": 0 },
        { "code": "OVACPOT-LG-GRA", "size": "Large | 600mm x 700mm", "color": "Granite", "base_price_rands": 2366.22, "stock_quantity": 0 },
        { "code": "OVACPOT-LG-GRA-2", "size": "Large | 600mm x 700mm", "color": "Granite Sealed", "base_price_rands": 2366.22, "stock_quantity": 0 },
        { "code": "OVACPOT-LG-ROC", "size": "Large | 600mm x 700mm", "color": "Rock", "base_price_rands": 2366.22, "stock_quantity": 0 },
        { "code": "OVACPOT-LG-VEL", "size": "Large | 600mm x 700mm", "color": "Velvet", "base_price_rands": 2366.22, "stock_quantity": 0 },
        { "code": "OVACPOT-LG-CHR", "size": "Large | 600mm x 700mm", "color": "Chryso Black", "base_price_rands": 2366.22, "stock_quantity": 0 },
        { "code": "OVACPOT-MD-AMP", "size": "Medium | 500mm X 600mm", "color": "Amper", "base_price_rands": 1946.29, "stock_quantity": 0 },
        { "code": "OVACPOT-MD-FWH", "size": "Medium | 500mm X 600mm", "color": "Flinted White", "base_price_rands": 1946.29, "stock_quantity": 0 },
        { "code": "OVACPOT-MD-GRA", "size": "Medium | 500mm X 600mm", "color": "Granite", "base_price_rands": 1946.29, "stock_quantity": 0 },
        { "code": "OVACPOT-MD-GRA-2", "size": "Medium | 500mm X 600mm", "color": "Granite Sealed", "base_price_rands": 1946.29, "stock_quantity": 0 },
        { "code": "OVACPOT-MD-ROC", "size": "Medium | 500mm X 600mm", "color": "Rock", "base_price_rands": 1946.29, "stock_quantity": 0 },
        { "code": "OVACPOT-MD-VEL", "size": "Medium | 500mm X 600mm", "color": "Velvet", "base_price_rands": 1946.29, "stock_quantity": 0 },
        { "code": "OVACPOT-MD-CHR", "size": "Medium | 500mm X 600mm", "color": "Chryso Black", "base_price_rands": 1946.29, "stock_quantity": 0 },
        { "code": "OVACPOT-SM-AMP", "size": "Small | 400mm X 500mm", "color": "Amper", "base_price_rands": 1226.42, "stock_quantity": 0 },
        { "code": "OVACPOT-SM-FWH", "size": "Small | 400mm X 500mm", "color": "Flinted White", "base_price_rands": 1226.42, "stock_quantity": 0 },
        { "code": "OVACPOT-SM-GRA", "size": "Small | 400mm X 500mm", "color": "Granite", "base_price_rands": 1226.42, "stock_quantity": 0 },
        { "code": "OVACPOT-SM-GRA-2", "size": "Small | 400mm X 500mm", "color": "Granite Sealed", "base_price_rands": 1226.42, "stock_quantity": 0 },
        { "code": "OVACPOT-SM-ROC", "size": "Small | 400mm X 500mm", "color": "Rock", "base_price_rands": 1226.42, "stock_quantity": 0 },
        { "code": "OVACPOT-SM-VEL", "size": "Small | 400mm X 500mm", "color": "Velvet", "base_price_rands": 1226.42, "stock_quantity": 0 },
        { "code": "OVACPOT-SM-CHR", "size": "Small | 400mm X 500mm", "color": "Chryso Black", "base_price_rands": 1226.42, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Nevada Trough Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "NEVTRCPOT-LG-AMP", "size": "Large | 300mm h x 420mm w x 700mm l", "color": "Amper", "base_price_rands": 1263.23, "stock_quantity": 0 },
        { "code": "NEVTRCPOT-LG-FWH", "size": "Large | 300mm h x 420mm w x 700mm l", "color": "Flinted White", "base_price_rands": 1263.23, "stock_quantity": 0 },
        { "code": "NEVTRCPOT-LG-GRA", "size": "Large | 300mm h x 420mm w x 700mm l", "color": "Granite", "base_price_rands": 1263.23, "stock_quantity": 0 },
        { "code": "NEVTRCPOT-LG-GRA-2", "size": "Large | 300mm h x 420mm w x 700mm l", "color": "Granite Sealed", "base_price_rands": 1263.23, "stock_quantity": 0 },
        { "code": "NEVTRCPOT-LG-ROC", "size": "Large | 300mm h x 420mm w x 700mm l", "color": "Rock", "base_price_rands": 1263.23, "stock_quantity": 0 },
        { "code": "NEVTRCPOT-LG-VEL", "size": "Large | 300mm h x 420mm w x 700mm l", "color": "Velvet", "base_price_rands": 1263.23, "stock_quantity": 0 },
        { "code": "NEVTRCPOT-LG-CHR", "size": "Large | 300mm h x 420mm w x 700mm l", "color": "Chryso Black", "base_price_rands": 1263.23, "stock_quantity": 0 },
        { "code": "NEVTRCPOT-SM-AMP", "size": "Small", "color": "Amper", "base_price_rands": 636.64, "stock_quantity": 0 },
        { "code": "NEVTRCPOT-SM-FWH", "size": "Small", "color": "Flinted White", "base_price_rands": 636.64, "stock_quantity": 0 },
        { "code": "NEVTRCPOT-SM-GRA", "size": "Small", "color": "Granite", "base_price_rands": 636.64, "stock_quantity": 0 },
        { "code": "NEVTRCPOT-SM-GRA-2", "size": "Small", "color": "Granite Sealed", "base_price_rands": 636.64, "stock_quantity": 0 },
        { "code": "NEVTRCPOT-SM-ROC", "size": "Small", "color": "Rock", "base_price_rands": 636.64, "stock_quantity": 0 },
        { "code": "NEVTRCPOT-SM-VEL", "size": "Small", "color": "Velvet", "base_price_rands": 636.64, "stock_quantity": 0 },
        { "code": "NEVTRCPOT-SM-CHR", "size": "Small", "color": "Chryso Black", "base_price_rands": 1263.23, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Premium Nevada Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "NEVCPOT-SM-AMP", "size": "Small | 850mm x 440mm", "color": "Amper", "base_price_rands": 1594.95, "stock_quantity": 0 },
        { "code": "NEVCPOT-SM-GRA", "size": "Small | 850mm x 440mm", "color": "Granite", "base_price_rands": 1594.95, "stock_quantity": 0 },
        { "code": "NEVCPOT-SM-GRA-2", "size": "Small | 850mm x 440mm", "color": "Granite Sealed", "base_price_rands": 1594.95, "stock_quantity": 0 },
        { "code": "NEVCPOT-SM-ROC", "size": "Small | 850mm x 440mm", "color": "Rock", "base_price_rands": 1594.95, "stock_quantity": 0 },
        { "code": "NEVCPOT-SM-VEL", "size": "Small | 850mm x 440mm", "color": "Velvet", "base_price_rands": 1594.95, "stock_quantity": 0 },
        { "code": "NEVCPOT-SM-FWH", "size": "Small | 850mm x 440mm", "color": "Flinted White", "base_price_rands": 1594.95, "stock_quantity": 0 },
        { "code": "NEVCPOT-SM-CHR", "size": "Small | 850mm x 440mm", "color": "Chryso Black", "base_price_rands": 1594.95, "stock_quantity": 0 },
        { "code": "NEVCPOT-MD-AMP", "size": "Medium | 1050mm x 470mm", "color": "Amper", "base_price_rands": 2104.27, "stock_quantity": 0 },
        { "code": "NEVCPOT-MD-GRA", "size": "Medium | 1050mm x 470mm", "color": "Granite", "base_price_rands": 2104.27, "stock_quantity": 0 },
        { "code": "NEVCPOT-MD-GRA-2", "size": "Medium | 1050mm x 470mm", "color": "Granite Sealed", "base_price_rands": 2104.27, "stock_quantity": 0 },
        { "code": "NEVCPOT-MD-ROC", "size": "Medium | 1050mm x 470mm", "color": "Rock", "base_price_rands": 2104.27, "stock_quantity": 0 },
        { "code": "NEVCPOT-MD-VEL", "size": "Medium | 1050mm x 470mm", "color": "Velvet", "base_price_rands": 2104.27, "stock_quantity": 0 },
        { "code": "NEVCPOT-MD-FWH", "size": "Medium | 1050mm x 470mm", "color": "Flinted White", "base_price_rands": 2104.27, "stock_quantity": 0 },
        { "code": "NEVCPOT-MD-CHR", "size": "Medium | 1050mm x 470mm", "color": "Chryso Black", "base_price_rands": 2104.27, "stock_quantity": 0 },
        { "code": "NEVCPOT-LG-AMP", "size": "Large | 1240mm x 500mm", "color": "Amper", "base_price_rands": 2449.39, "stock_quantity": 0 },
        { "code": "NEVCPOT-LG-GRA", "size": "Large | 1240mm x 500mm", "color": "Granite", "base_price_rands": 2449.39, "stock_quantity": 0 },
        { "code": "NEVCPOT-LG-GRA-2", "size": "Large | 1240mm x 500mm", "color": "Granite Sealed", "base_price_rands": 2449.39, "stock_quantity": 0 },
        { "code": "NEVCPOT-LG-ROC", "size": "Large | 1240mm x 500mm", "color": "Rock", "base_price_rands": 2449.39, "stock_quantity": 0 },
        { "code": "NEVCPOT-LG-VEL", "size": "Large | 1240mm x 500mm", "color": "Velvet", "base_price_rands": 2449.39, "stock_quantity": 0 },
        { "code": "NEVCPOT-LG-FWH", "size": "Large | 1240mm x 500mm", "color": "Flinted White", "base_price_rands": 2449.39, "stock_quantity": 0 },
        { "code": "NEVCPOT-LG-CHR", "size": "Large | 1240mm x 500mm", "color": "Chryso Black", "base_price_rands": 2449.39, "stock_quantity": 0 },
        { "code": "NEVCPOT-1800-AMP", "size": "Jumbo | 1800mm x 640mm", "color": "Amper", "base_price_rands": 4838.49, "stock_quantity": 0 },
        { "code": "NEVCPOT-1800-GRA", "size": "Jumbo | 1800mm x 640mm", "color": "Granite", "base_price_rands": 4838.49, "stock_quantity": 0 },
        { "code": "NEVCPOT-1800-GRA-2", "size": "Jumbo | 1800mm x 640mm", "color": "Granite Sealed", "base_price_rands": 4838.49, "stock_quantity": 0 },
        { "code": "NEVCPOT-1800-ROC", "size": "Jumbo | 1800mm x 640mm", "color": "Rock", "base_price_rands": 4838.49, "stock_quantity": 0 },
        { "code": "NEVCPOT-1800-VEL", "size": "Jumbo | 1800mm x 640mm", "color": "Velvet", "base_price_rands": 4838.49, "stock_quantity": 0 },
        { "code": "NEVCPOT-1800-FWH", "size": "Jumbo | 1800mm x 640mm", "color": "Flinted White", "base_price_rands": 4838.49, "stock_quantity": 0 },
        { "code": "NEVCPOT-1800-CHR", "size": "Jumbo | 1800mm x 640mm", "color": "Chryso Black", "base_price_rands": 4838.49, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Nebraska Concrete Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "NEBCPOT-LG-AMP", "size": "Large | 1140mm x 490mm", "color": "Amper", "base_price_rands": 3001.7, "stock_quantity": 0 },
        { "code": "NEBCPOT-LG-FWH", "size": "Large | 1140mm x 490mm", "color": "Flinted White", "base_price_rands": 3001.7, "stock_quantity": 0 },
        { "code": "NEBCPOT-LG-GRA", "size": "Large | 1140mm x 490mm", "color": "Granite", "base_price_rands": 3001.7, "stock_quantity": 0 },
        { "code": "NEBCPOT-LG-GRA-2", "size": "Large | 1140mm x 490mm", "color": "Granite Sealed", "base_price_rands": 3001.7, "stock_quantity": 0 },
        { "code": "NEBCPOT-LG-ROC", "size": "Large | 1140mm x 490mm", "color": "Rock", "base_price_rands": 3001.7, "stock_quantity": 0 },
        { "code": "NEBCPOT-LG-VEL", "size": "Large | 1140mm x 490mm", "color": "Velvet", "base_price_rands": 3001.7, "stock_quantity": 0 },
        { "code": "NEBCPOT-LG-CHR", "size": "Large | 1140mm x 490mm", "color": "Chryso Black", "base_price_rands": 3001.7, "stock_quantity": 0 },
        { "code": "NEBCPOT-MD-AMP", "size": "Medium | 930mm x 400m", "color": "Amper", "base_price_rands": 2035.87, "stock_quantity": 0 },
        { "code": "NEBCPOT-MD-FWH", "size": "Medium | 930mm x 400m", "color": "Flinted White", "base_price_rands": 2035.87, "stock_quantity": 0 },
        { "code": "NEBCPOT-MD-GRA", "size": "Medium | 930mm x 400m", "color": "Granite", "base_price_rands": 2035.87, "stock_quantity": 0 },
        { "code": "NEBCPOT-MD-GRA-2", "size": "Medium | 930mm x 400m", "color": "Granite Sealed", "base_price_rands": 2035.87, "stock_quantity": 0 },
        { "code": "NEBCPOT-MD-ROC", "size": "Medium | 930mm x 400m", "color": "Rock", "base_price_rands": 2035.87, "stock_quantity": 0 },
        { "code": "NEBCPOT-MD-VEL", "size": "Medium | 930mm x 400m", "color": "Velvet", "base_price_rands": 2035.87, "stock_quantity": 0 },
        { "code": "NEBCPOT-MD-CHR", "size": "Medium | 930mm x 400m", "color": "Chryso Black", "base_price_rands": 2035.87, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Monica Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "MONCPOT-LG-FWH", "size": "Large | 590mm x 610mm", "color": "flinted white", "base_price_rands": 2479.57, "stock_quantity": 0 },
        { "code": "MONCPOT-LG-CHR", "size": "Large | 590mm x 610mm", "color": "Chryso Black", "base_price_rands": 2479.57, "stock_quantity": 0 },
        { "code": "MONCPOT-LG-GRA", "size": "Large | 590mm x 610mm", "color": "Granite Dark Smooth", "base_price_rands": 2479.57, "stock_quantity": 0 },
        { "code": "MONCPOT-LG-AMP", "size": "Large | 590mm x 610mm", "color": "Amper", "base_price_rands": 2479.57, "stock_quantity": 0 },
        { "code": "MONCPOT-LG-GRA-2", "size": "Large | 590mm x 610mm", "color": "Granite Rough", "base_price_rands": 2479.57, "stock_quantity": 0 },
        { "code": "MONCPOT-LG-RAW", "size": "Large | 590mm x 610mm", "color": "Raw", "base_price_rands": 2479.57, "stock_quantity": 0 },
        { "code": "MONCPOT-MD-FWH", "size": "Medium | 500mm x 480mm", "color": "flinted white", "base_price_rands": 1276.43, "stock_quantity": 0 },
        { "code": "MONCPOT-MD-CHR", "size": "Medium | 500mm x 480mm", "color": "Chryso Black", "base_price_rands": 1276.43, "stock_quantity": 0 },
        { "code": "MONCPOT-MD-GRA", "size": "Medium | 500mm x 480mm", "color": "Granite Dark Smooth", "base_price_rands": 1276.43, "stock_quantity": 0 },
        { "code": "MONCPOT-MD-AMP", "size": "Medium | 500mm x 480mm", "color": "Amper", "base_price_rands": 1276.43, "stock_quantity": 0 },
        { "code": "MONCPOT-MD-GRA-2", "size": "Medium | 500mm x 480mm", "color": "Granite Rough", "base_price_rands": 1276.43, "stock_quantity": 0 },
        { "code": "MONCPOT-MD-RAW", "size": "Medium | 500mm x 480mm", "color": "Raw", "base_price_rands": 1276.43, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Millstone Concrete Pot/Pond",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "MILCPOT-LG-AMP", "size": "Large | 900mm X 400mm", "color": "amper", "base_price_rands": 3803.63, "stock_quantity": 0 },
        { "code": "MILCPOT-LG-ANT", "size": "Large | 900mm X 400mm", "color": "antique rust", "base_price_rands": 3803.63, "stock_quantity": 0 },
        { "code": "MILCPOT-LG-BRO", "size": "Large | 900mm X 400mm", "color": "bronze", "base_price_rands": 3803.63, "stock_quantity": 0 },
        { "code": "MILCPOT-LG-CHR", "size": "Large | 900mm X 400mm", "color": "charcoal", "base_price_rands": 3803.63, "stock_quantity": 0 },
        { "code": "MILCPOT-LG-CHR-2", "size": "Large | 900mm X 400mm", "color": "chryso black", "base_price_rands": 3803.63, "stock_quantity": 0 },
        { "code": "MILCPOT-LG-GRA", "size": "Large | 900mm X 400mm", "color": "granite", "base_price_rands": 3803.63, "stock_quantity": 0 },
        { "code": "MILCPOT-LG-ROC", "size": "Large | 900mm X 400mm", "color": "rock", "base_price_rands": 3803.63, "stock_quantity": 0 },
        { "code": "MILCPOT-LG-VEL", "size": "Large | 900mm X 400mm", "color": "velvet", "base_price_rands": 3803.63, "stock_quantity": 0 },
        { "code": "MILCPOT-LG-RAW", "size": "Large | 900mm X 400mm", "color": "raw", "base_price_rands": 3803.63, "stock_quantity": 0 },
        { "code": "MILCPOT-SM-AMP", "size": "Small | 600mm X 250mm", "color": "amper", "base_price_rands": 1559.69, "stock_quantity": 0 },
        { "code": "MILCPOT-SM-ANT", "size": "Small | 600mm X 250mm", "color": "antique rust", "base_price_rands": 1559.69, "stock_quantity": 0 },
        { "code": "MILCPOT-SM-BRO", "size": "Small | 600mm X 250mm", "color": "bronze", "base_price_rands": 1559.69, "stock_quantity": 0 },
        { "code": "MILCPOT-SM-CHR", "size": "Small | 600mm X 250mm", "color": "charcoal", "base_price_rands": 1559.69, "stock_quantity": 0 },
        { "code": "MILCPOT-SM-CHR-2", "size": "Small | 600mm X 250mm", "color": "chryso black", "base_price_rands": 1559.69, "stock_quantity": 0 },
        { "code": "MILCPOT-SM-GRA", "size": "Small | 600mm X 250mm", "color": "granite", "base_price_rands": 1559.69, "stock_quantity": 0 },
        { "code": "MILCPOT-SM-ROC", "size": "Small | 600mm X 250mm", "color": "rock", "base_price_rands": 1559.69, "stock_quantity": 0 },
        { "code": "MILCPOT-SM-VEL", "size": "Small | 600mm X 250mm", "color": "velvet", "base_price_rands": 1559.69, "stock_quantity": 0 },
        { "code": "MILCPOT-SM-RAW", "size": "Small | 600mm X 250mm", "color": "raw", "base_price_rands": 1559.69, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Mexican Concrete Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "MEXCPOT-1500-AMP", "size": "Giant | 1500mm X 600mm", "color": "Amper", "base_price_rands": 3417.76, "stock_quantity": 0 },
        { "code": "MEXCPOT-1500-FWH", "size": "Giant | 1500mm X 600mm", "color": "Flinted White", "base_price_rands": 3417.76, "stock_quantity": 0 },
        { "code": "MEXCPOT-1500-GRA", "size": "Giant | 1500mm X 600mm", "color": "Granite", "base_price_rands": 3417.76, "stock_quantity": 0 },
        { "code": "MEXCPOT-1500-GRA-2", "size": "Giant | 1500mm X 600mm", "color": "Granite Sealed", "base_price_rands": 3417.76, "stock_quantity": 0 },
        { "code": "MEXCPOT-1500-ROC", "size": "Giant | 1500mm X 600mm", "color": "Rock", "base_price_rands": 3417.76, "stock_quantity": 0 },
        { "code": "MEXCPOT-1500-VEL", "size": "Giant | 1500mm X 600mm", "color": "Velvet", "base_price_rands": 3417.76, "stock_quantity": 0 },
        { "code": "MEXCPOT-LG-AMP", "size": "Large | 1100mm X 450mm", "color": "Amper", "base_price_rands": 2375.67, "stock_quantity": 0 },
        { "code": "MEXCPOT-LG-FWH", "size": "Large | 1100mm X 450mm", "color": "Flinted White", "base_price_rands": 2375.67, "stock_quantity": 0 },
        { "code": "MEXCPOT-LG-GRA", "size": "Large | 1100mm X 450mm", "color": "Granite", "base_price_rands": 2375.67, "stock_quantity": 0 },
        { "code": "MEXCPOT-LG-GRA-2", "size": "Large | 1100mm X 450mm", "color": "Granite Sealed", "base_price_rands": 2375.67, "stock_quantity": 0 },
        { "code": "MEXCPOT-LG-ROC", "size": "Large | 1100mm X 450mm", "color": "Rock", "base_price_rands": 2375.67, "stock_quantity": 0 },
        { "code": "MEXCPOT-LG-VEL", "size": "Large | 1100mm X 450mm", "color": "Velvet", "base_price_rands": 2375.67, "stock_quantity": 0 },
        { "code": "MEXCPOT-MD-AMP", "size": "Medium | 960mm X 390mm", "color": "Amper", "base_price_rands": 1759.13, "stock_quantity": 0 },
        { "code": "MEXCPOT-MD-FWH", "size": "Medium | 960mm X 390mm", "color": "Flinted White", "base_price_rands": 1759.13, "stock_quantity": 0 },
        { "code": "MEXCPOT-MD-GRA", "size": "Medium | 960mm X 390mm", "color": "Granite", "base_price_rands": 1759.13, "stock_quantity": 0 },
        { "code": "MEXCPOT-MD-GRA-2", "size": "Medium | 960mm X 390mm", "color": "Granite Sealed", "base_price_rands": 1759.13, "stock_quantity": 0 },
        { "code": "MEXCPOT-MD-ROC", "size": "Medium | 960mm X 390mm", "color": "Rock", "base_price_rands": 1759.13, "stock_quantity": 0 },
        { "code": "MEXCPOT-MD-VEL", "size": "Medium | 960mm X 390mm", "color": "Velvet", "base_price_rands": 1759.13, "stock_quantity": 0 },
        { "code": "MEXCPOT-SM-AMP", "size": "Small | 820mm X 350mm", "color": "Amper", "base_price_rands": 1216.33, "stock_quantity": 0 },
        { "code": "MEXCPOT-SM-FWH", "size": "Small | 820mm X 350mm", "color": "Flinted White", "base_price_rands": 1216.33, "stock_quantity": 0 },
        { "code": "MEXCPOT-SM-GRA", "size": "Small | 820mm X 350mm", "color": "Granite", "base_price_rands": 1216.33, "stock_quantity": 0 },
        { "code": "MEXCPOT-SM-GRA-2", "size": "Small | 820mm X 350mm", "color": "Granite Sealed", "base_price_rands": 1216.33, "stock_quantity": 0 },
        { "code": "MEXCPOT-SM-ROC", "size": "Small | 820mm X 350mm", "color": "Rock", "base_price_rands": 1216.33, "stock_quantity": 0 },
        { "code": "MEXCPOT-SM-VEL", "size": "Small | 820mm X 350mm", "color": "Velvet", "base_price_rands": 1216.33, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Lilly Pond Concrete Pond",
      "category": "Pond",
      "description_html": "",
      "skus": [
        { "code": "LILPONCPOT-LG-AMP", "size": "Large | 400mm x 1240mm", "color": "Amper", "base_price_rands": 2586.77, "stock_quantity": 0 },
        { "code": "LILPONCPOT-LG-FWH", "size": "Large | 400mm x 1240mm", "color": "Flinted White", "base_price_rands": 2586.77, "stock_quantity": 0 },
        { "code": "LILPONCPOT-LG-GRL", "size": "Large | 400mm x 1240mm", "color": "Granite Light", "base_price_rands": 2586.77, "stock_quantity": 0 },
        { "code": "LILPONCPOT-LG-GRD", "size": "Large | 400mm x 1240mm", "color": "Granite Dark", "base_price_rands": 2586.77, "stock_quantity": 0 },
        { "code": "LILPONCPOT-LG-ROC", "size": "Large | 400mm x 1240mm", "color": "Rock", "base_price_rands": 2586.77, "stock_quantity": 0 },
        { "code": "LILPONCPOT-LG-VEL", "size": "Large | 400mm x 1240mm", "color": "Velvet", "base_price_rands": 2586.77, "stock_quantity": 0 },
        { "code": "LILPONCPOT-LG-CHR", "size": "Large | 400mm x 1240mm", "color": "Chryso Black", "base_price_rands": 2586.77, "stock_quantity": 0 },
        { "code": "LILPONCPOT-LG-GRA", "size": "Large | 400mm x 1240mm", "color": "Granite dark sealed", "base_price_rands": 2586.77, "stock_quantity": 0 },
        { "code": "LILPONCPOT-LG-GRA-2", "size": "Large | 400mm x 1240mm", "color": "Granite light sealed", "base_price_rands": 2586.77, "stock_quantity": 0 },
        { "code": "LILPONCPOT-MD-AMP", "size": "Medium | 300mm x 1020mm", "color": "Amper", "base_price_rands": 1846.27, "stock_quantity": 0 },
        { "code": "LILPONCPOT-MD-FWH", "size": "Medium | 300mm x 1020mm", "color": "Flinted White", "base_price_rands": 1846.27, "stock_quantity": 0 },
        { "code": "LILPONCPOT-MD-GRL", "size": "Medium | 300mm x 1020mm", "color": "Granite Light", "base_price_rands": 1846.27, "stock_quantity": 0 },
        { "code": "LILPONCPOT-MD-GRD", "size": "Medium | 300mm x 1020mm", "color": "Granite Dark", "base_price_rands": 1846.27, "stock_quantity": 0 },
        { "code": "LILPONCPOT-MD-ROC", "size": "Medium | 300mm x 1020mm", "color": "Rock", "base_price_rands": 1846.27, "stock_quantity": 0 },
        { "code": "LILPONCPOT-MD-VEL", "size": "Medium | 300mm x 1020mm", "color": "Velvet", "base_price_rands": 1846.27, "stock_quantity": 0 },
        { "code": "LILPONCPOT-MD-CHR", "size": "Medium | 300mm x 1020mm", "color": "Chryso Black", "base_price_rands": 1846.27, "stock_quantity": 0 },
        { "code": "LILPONCPOT-MD-GRA", "size": "Medium | 300mm x 1020mm", "color": "Granite dark sealed", "base_price_rands": 1846.27, "stock_quantity": 0 },
        { "code": "LILPONCPOT-MD-GRA-2", "size": "Medium | 300mm x 1020mm", "color": "Granite light sealed", "base_price_rands": 1846.27, "stock_quantity": 0 },
        { "code": "LILPONCPOT-SM-AMP", "size": "Small | 230mm x 720mm", "color": "Amper", "base_price_rands": 727.1, "stock_quantity": 0 },
        { "code": "LILPONCPOT-SM-FWH", "size": "Small | 230mm x 720mm", "color": "Flinted White", "base_price_rands": 727.1, "stock_quantity": 0 },
        { "code": "LILPONCPOT-SM-GRL", "size": "Small | 230mm x 720mm", "color": "Granite Light", "base_price_rands": 727.1, "stock_quantity": 0 },
        { "code": "LILPONCPOT-SM-GRD", "size": "Small | 230mm x 720mm", "color": "Granite Dark", "base_price_rands": 727.1, "stock_quantity": 0 },
        { "code": "LILPONCPOT-SM-ROC", "size": "Small | 230mm x 720mm", "color": "Rock", "base_price_rands": 727.1, "stock_quantity": 0 },
        { "code": "LILPONCPOT-SM-VEL", "size": "Small | 230mm x 720mm", "color": "Velvet", "base_price_rands": 727.1, "stock_quantity": 0 },
        { "code": "LILPONCPOT-SM-CHR", "size": "Small | 230mm x 720mm", "color": "Chryso Black", "base_price_rands": 727.1, "stock_quantity": 0 },
        { "code": "LILPONCPOT-SM-GRA", "size": "Small | 230mm x 720mm", "color": "Granite dark sealed", "base_price_rands": 727.1, "stock_quantity": 0 },
        { "code": "LILPONCPOT-SM-GRA-2", "size": "Small | 230mm x 720mm", "color": "Granite light sealed", "base_price_rands": 727.1, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Kathy Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "KATCPOT-LG-AMP", "size": "Large | 530mm x 555mm", "color": "Amper", "base_price_rands": 1052.13, "stock_quantity": 0 },
        { "code": "KATCPOT-LG-FWH", "size": "Large | 530mm x 555mm", "color": "Flinted White", "base_price_rands": 1052.13, "stock_quantity": 0 },
        { "code": "KATCPOT-LG-GRA", "size": "Large | 530mm x 555mm", "color": "Granite", "base_price_rands": 1052.13, "stock_quantity": 0 },
        { "code": "KATCPOT-LG-GRA-2", "size": "Large | 530mm x 555mm", "color": "Granite Sealed", "base_price_rands": 1052.13, "stock_quantity": 0 },
        { "code": "KATCPOT-LG-ROC", "size": "Large | 530mm x 555mm", "color": "Rock", "base_price_rands": 1052.13, "stock_quantity": 0 },
        { "code": "KATCPOT-LG-VEL", "size": "Large | 530mm x 555mm", "color": "Velvet", "base_price_rands": 1052.13, "stock_quantity": 0 },
        { "code": "KATCPOT-MD-AMP", "size": "Medium | 445mm X 450mm", "color": "Amper", "base_price_rands": 673.48, "stock_quantity": 0 },
        { "code": "KATCPOT-MD-FWH", "size": "Medium | 445mm X 450mm", "color": "Flinted White", "base_price_rands": 673.48, "stock_quantity": 0 },
        { "code": "KATCPOT-MD-GRA", "size": "Medium | 445mm X 450mm", "color": "Granite", "base_price_rands": 673.48, "stock_quantity": 0 },
        { "code": "KATCPOT-MD-GRA-2", "size": "Medium | 445mm X 450mm", "color": "Granite Sealed", "base_price_rands": 673.48, "stock_quantity": 0 },
        { "code": "KATCPOT-MD-ROC", "size": "Medium | 445mm X 450mm", "color": "Rock", "base_price_rands": 673.48, "stock_quantity": 0 },
        { "code": "KATCPOT-MD-VEL", "size": "Medium | 445mm X 450mm", "color": "Velvet", "base_price_rands": 673.48, "stock_quantity": 0 },
        { "code": "KATCPOT-SM-AMP", "size": "Small | 355mm x 355mm", "color": "Amper", "base_price_rands": 418.84, "stock_quantity": 0 },
        { "code": "KATCPOT-SM-FWH", "size": "Small | 355mm x 355mm", "color": "Flinted White", "base_price_rands": 418.84, "stock_quantity": 0 },
        { "code": "KATCPOT-SM-GRA", "size": "Small | 355mm x 355mm", "color": "Granite", "base_price_rands": 418.84, "stock_quantity": 0 },
        { "code": "KATCPOT-SM-GRA-2", "size": "Small | 355mm x 355mm", "color": "Granite Sealed", "base_price_rands": 418.84, "stock_quantity": 0 },
        { "code": "KATCPOT-SM-ROC", "size": "Small | 355mm x 355mm", "color": "Rock", "base_price_rands": 418.84, "stock_quantity": 0 },
        { "code": "KATCPOT-SM-VEL", "size": "Small | 355mm x 355mm", "color": "Velvet", "base_price_rands": 418.84, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Jessica Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "JESCPOT-600-AMP", "size": "Jumbo | 600mm X 710mm", "color": "Amper", "base_price_rands": 1566.36, "stock_quantity": 0 },
        { "code": "JESCPOT-600-FWH", "size": "Jumbo | 600mm X 710mm", "color": "Flinted White", "base_price_rands": 1566.36, "stock_quantity": 0 },
        { "code": "JESCPOT-600-GRA", "size": "Jumbo | 600mm X 710mm", "color": "Granite", "base_price_rands": 1566.36, "stock_quantity": 0 },
        { "code": "JESCPOT-600-GRA-2", "size": "Jumbo | 600mm X 710mm", "color": "Granite Sealed", "base_price_rands": 1566.36, "stock_quantity": 0 },
        { "code": "JESCPOT-600-ROC", "size": "Jumbo | 600mm X 710mm", "color": "Rock", "base_price_rands": 1566.36, "stock_quantity": 0 },
        { "code": "JESCPOT-600-VEL", "size": "Jumbo | 600mm X 710mm", "color": "Velvet", "base_price_rands": 1566.36, "stock_quantity": 0 },
        { "code": "JESCPOT-600-CHR", "size": "Jumbo | 600mm X 710mm", "color": "Chryso Black", "base_price_rands": 1566.36, "stock_quantity": 0 },
        { "code": "JESCPOT-LG-AMP", "size": "Large | 480mm X 515mm", "color": "Amper", "base_price_rands": 918.1, "stock_quantity": 0 },
        { "code": "JESCPOT-LG-FWH", "size": "Large | 480mm X 515mm", "color": "Flinted White", "base_price_rands": 918.1, "stock_quantity": 0 },
        { "code": "JESCPOT-LG-GRA", "size": "Large | 480mm X 515mm", "color": "Granite", "base_price_rands": 918.1, "stock_quantity": 0 },
        { "code": "JESCPOT-LG-GRA-2", "size": "Large | 480mm X 515mm", "color": "Granite Sealed", "base_price_rands": 918.1, "stock_quantity": 0 },
        { "code": "JESCPOT-LG-ROC", "size": "Large | 480mm X 515mm", "color": "Rock", "base_price_rands": 918.1, "stock_quantity": 0 },
        { "code": "JESCPOT-LG-VEL", "size": "Large | 480mm X 515mm", "color": "Velvet", "base_price_rands": 918.1, "stock_quantity": 0 },
        { "code": "JESCPOT-LG-CHR", "size": "Large | 480mm X 515mm", "color": "Chryso Black", "base_price_rands": 1574.85, "stock_quantity": 0 },
        { "code": "JESCPOT-MD-AMP", "size": "Medium | 360mm X 417mm", "color": "Amper", "base_price_rands": 578.14, "stock_quantity": 0 },
        { "code": "JESCPOT-MD-FWH", "size": "Medium | 360mm X 417mm", "color": "Flinted White", "base_price_rands": 578.14, "stock_quantity": 0 },
        { "code": "JESCPOT-MD-GRA", "size": "Medium | 360mm X 417mm", "color": "Granite", "base_price_rands": 578.14, "stock_quantity": 0 },
        { "code": "JESCPOT-MD-GRA-2", "size": "Medium | 360mm X 417mm", "color": "Granite Sealed", "base_price_rands": 578.14, "stock_quantity": 0 },
        { "code": "JESCPOT-MD-ROC", "size": "Medium | 360mm X 417mm", "color": "Rock", "base_price_rands": 578.14, "stock_quantity": 0 },
        { "code": "JESCPOT-MD-VEL", "size": "Medium | 360mm X 417mm", "color": "Velvet", "base_price_rands": 578.14, "stock_quantity": 0 },
        { "code": "JESCPOT-MD-CHR", "size": "Medium | 360mm X 417mm", "color": "Chryso Black", "base_price_rands": 578.14, "stock_quantity": 0 },
        { "code": "JESCPOT-SM-AMP", "size": "Small", "color": "Amper", "base_price_rands": 317.34, "stock_quantity": 0 },
        { "code": "JESCPOT-SM-FWH", "size": "Small", "color": "Flinted White", "base_price_rands": 317.34, "stock_quantity": 0 },
        { "code": "JESCPOT-SM-GRA", "size": "Small", "color": "Granite", "base_price_rands": 317.34, "stock_quantity": 0 },
        { "code": "JESCPOT-SM-GRA-2", "size": "Small", "color": "Granite Sealed", "base_price_rands": 317.34, "stock_quantity": 0 },
        { "code": "JESCPOT-SM-ROC", "size": "Small", "color": "Rock", "base_price_rands": 317.34, "stock_quantity": 0 },
        { "code": "JESCPOT-SM-VEL", "size": "Small", "color": "Velvet", "base_price_rands": 317.34, "stock_quantity": 0 },
        { "code": "JESCPOT-SM-CHR", "size": "Small", "color": "Chryso Black", "base_price_rands": 317.34, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Italia Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "ITACPOT-LG-AMP", "size": "Large | 500mm x 565mm", "color": "Amper", "base_price_rands": 1203.11, "stock_quantity": 0 },
        { "code": "ITACPOT-LG-FWH", "size": "Large | 500mm x 565mm", "color": "Flinted White", "base_price_rands": 1203.11, "stock_quantity": 0 },
        { "code": "ITACPOT-LG-GRA", "size": "Large | 500mm x 565mm", "color": "Granite", "base_price_rands": 1203.11, "stock_quantity": 0 },
        { "code": "ITACPOT-LG-GRA-2", "size": "Large | 500mm x 565mm", "color": "Granite Sealed", "base_price_rands": 1203.11, "stock_quantity": 0 },
        { "code": "ITACPOT-LG-ROC", "size": "Large | 500mm x 565mm", "color": "Rock", "base_price_rands": 1203.11, "stock_quantity": 0 },
        { "code": "ITACPOT-LG-VEL", "size": "Large | 500mm x 565mm", "color": "Velvet", "base_price_rands": 1203.11, "stock_quantity": 0 },
        { "code": "ITACPOT-LG-CHR", "size": "Large | 500mm x 565mm", "color": "Chryso Black", "base_price_rands": 1203.11, "stock_quantity": 0 },
        { "code": "ITACPOT-MD-AMP", "size": "Medium | 410mm x 500mm", "color": "Amper", "base_price_rands": 760.62, "stock_quantity": 0 },
        { "code": "ITACPOT-MD-FWH", "size": "Medium | 410mm x 500mm", "color": "Flinted White", "base_price_rands": 760.62, "stock_quantity": 0 },
        { "code": "ITACPOT-MD-GRA", "size": "Medium | 410mm x 500mm", "color": "Granite", "base_price_rands": 760.62, "stock_quantity": 0 },
        { "code": "ITACPOT-MD-GRA-2", "size": "Medium | 410mm x 500mm", "color": "Granite Sealed", "base_price_rands": 760.62, "stock_quantity": 0 },
        { "code": "ITACPOT-MD-ROC", "size": "Medium | 410mm x 500mm", "color": "Rock", "base_price_rands": 760.62, "stock_quantity": 0 },
        { "code": "ITACPOT-MD-VEL", "size": "Medium | 410mm x 500mm", "color": "Velvet", "base_price_rands": 760.62, "stock_quantity": 0 },
        { "code": "ITACPOT-MD-CHR", "size": "Medium | 410mm x 500mm", "color": "Chryso Black", "base_price_rands": 760.62, "stock_quantity": 0 },
        { "code": "ITACPOT-SM-AMP", "size": "Small | 340mm x 420mm", "color": "Amper", "base_price_rands": 569.9, "stock_quantity": 0 },
        { "code": "ITACPOT-SM-FWH", "size": "Small | 340mm x 420mm", "color": "Flinted White", "base_price_rands": 569.9, "stock_quantity": 0 },
        { "code": "ITACPOT-SM-GRA", "size": "Small | 340mm x 420mm", "color": "Granite", "base_price_rands": 569.9, "stock_quantity": 0 },
        { "code": "ITACPOT-SM-GRA-2", "size": "Small | 340mm x 420mm", "color": "Granite Sealed", "base_price_rands": 569.9, "stock_quantity": 0 },
        { "code": "ITACPOT-SM-ROC", "size": "Small | 340mm x 420mm", "color": "Rock", "base_price_rands": 569.9, "stock_quantity": 0 },
        { "code": "ITACPOT-SM-VEL", "size": "Small | 340mm x 420mm", "color": "Velvet", "base_price_rands": 569.9, "stock_quantity": 0 },
        { "code": "ITACPOT-SM-CHR", "size": "Small | 340mm x 420mm", "color": "Chryso Black", "base_price_rands": 569.9, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Hyena Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "HYECPOT-LG-AMP", "size": "Large | 670mm x 420mm", "color": "Amper", "base_price_rands": 1118.25, "stock_quantity": 0 },
        { "code": "HYECPOT-LG-FWH", "size": "Large | 670mm x 420mm", "color": "Flinted White", "base_price_rands": 1118.25, "stock_quantity": 0 },
        { "code": "HYECPOT-LG-GRA", "size": "Large | 670mm x 420mm", "color": "Granite", "base_price_rands": 1118.25, "stock_quantity": 0 },
        { "code": "HYECPOT-LG-GRA-2", "size": "Large | 670mm x 420mm", "color": "Granite Sealed", "base_price_rands": 1118.25, "stock_quantity": 0 },
        { "code": "HYECPOT-LG-ROC", "size": "Large | 670mm x 420mm", "color": "Rock", "base_price_rands": 1118.25, "stock_quantity": 0 },
        { "code": "HYECPOT-LG-VEL", "size": "Large | 670mm x 420mm", "color": "Velvet", "base_price_rands": 1118.25, "stock_quantity": 0 },
        { "code": "HYECPOT-MD-AMP", "size": "Medium | 570mm X 420mm", "color": "Amper", "base_price_rands": 952.58, "stock_quantity": 0 },
        { "code": "HYECPOT-MD-FWH", "size": "Medium | 570mm X 420mm", "color": "Flinted White", "base_price_rands": 952.58, "stock_quantity": 0 },
        { "code": "HYECPOT-MD-GRA", "size": "Medium | 570mm X 420mm", "color": "Granite", "base_price_rands": 952.58, "stock_quantity": 0 },
        { "code": "HYECPOT-MD-GRA-2", "size": "Medium | 570mm X 420mm", "color": "Granite Sealed", "base_price_rands": 952.58, "stock_quantity": 0 },
        { "code": "HYECPOT-MD-ROC", "size": "Medium | 570mm X 420mm", "color": "Rock", "base_price_rands": 952.58, "stock_quantity": 0 },
        { "code": "HYECPOT-MD-VEL", "size": "Medium | 570mm X 420mm", "color": "Velvet", "base_price_rands": 952.58, "stock_quantity": 0 },
        { "code": "HYECPOT-SM-AMP", "size": "Small | 460mm X 320mm", "color": "Amper", "base_price_rands": 621.25, "stock_quantity": 0 },
        { "code": "HYECPOT-SM-FWH", "size": "Small | 460mm X 320mm", "color": "Flinted White", "base_price_rands": 621.25, "stock_quantity": 0 },
        { "code": "HYECPOT-SM-GRA", "size": "Small | 460mm X 320mm", "color": "Granite", "base_price_rands": 621.25, "stock_quantity": 0 },
        { "code": "HYECPOT-SM-GRA-2", "size": "Small | 460mm X 320mm", "color": "Granite Sealed", "base_price_rands": 621.25, "stock_quantity": 0 },
        { "code": "HYECPOT-SM-ROC", "size": "Small | 460mm X 320mm", "color": "Rock", "base_price_rands": 621.25, "stock_quantity": 0 },
        { "code": "HYECPOT-SM-VEL", "size": "Small | 460mm X 320mm", "color": "Velvet", "base_price_rands": 621.25, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Honey Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "HONCPOT-LG-AMP", "size": "Large | 460mm X 430mm", "color": "amper", "base_price_rands": 645.0, "stock_quantity": 0 },
        { "code": "HONCPOT-LG-ANT", "size": "Large | 460mm X 430mm", "color": "antique rust", "base_price_rands": 645.0, "stock_quantity": 0 },
        { "code": "HONCPOT-LG-BRO", "size": "Large | 460mm X 430mm", "color": "bronze", "base_price_rands": 645.0, "stock_quantity": 0 },
        { "code": "HONCPOT-LG-CHR", "size": "Large | 460mm X 430mm", "color": "charcoal", "base_price_rands": 645.0, "stock_quantity": 0 },
        { "code": "HONCPOT-LG-CHR-2", "size": "Large | 460mm X 430mm", "color": "chryso black", "base_price_rands": 645.0, "stock_quantity": 0 },
        { "code": "HONCPOT-LG-GRA", "size": "Large | 460mm X 430mm", "color": "granite", "base_price_rands": 645.0, "stock_quantity": 0 },
        { "code": "HONCPOT-LG-ROC", "size": "Large | 460mm X 430mm", "color": "rock", "base_price_rands": 645.0, "stock_quantity": 0 },
        { "code": "HONCPOT-LG-VEL", "size": "Large | 460mm X 430mm", "color": "velvet", "base_price_rands": 645.0, "stock_quantity": 0 },
        { "code": "HONCPOT-LG-RAW", "size": "Large | 460mm X 430mm", "color": "raw", "base_price_rands": 645.0, "stock_quantity": 0 },
        { "code": "HONCPOT-MD-AMP", "size": "Medium | 360mm X 330mm", "color": "amper", "base_price_rands": 438.5, "stock_quantity": 0 },
        { "code": "HONCPOT-MD-ANT", "size": "Medium | 360mm X 330mm", "color": "antique rust", "base_price_rands": 438.5, "stock_quantity": 0 },
        { "code": "HONCPOT-MD-BRO", "size": "Medium | 360mm X 330mm", "color": "bronze", "base_price_rands": 438.5, "stock_quantity": 0 },
        { "code": "HONCPOT-MD-CHR", "size": "Medium | 360mm X 330mm", "color": "charcoal", "base_price_rands": 438.5, "stock_quantity": 0 },
        { "code": "HONCPOT-MD-CHR-2", "size": "Medium | 360mm X 330mm", "color": "chryso black", "base_price_rands": 438.5, "stock_quantity": 0 },
        { "code": "HONCPOT-MD-GRA", "size": "Medium | 360mm X 330mm", "color": "granite", "base_price_rands": 438.5, "stock_quantity": 0 },
        { "code": "HONCPOT-MD-ROC", "size": "Medium | 360mm X 330mm", "color": "rock", "base_price_rands": 438.5, "stock_quantity": 0 },
        { "code": "HONCPOT-MD-VEL", "size": "Medium | 360mm X 330mm", "color": "velvet", "base_price_rands": 438.5, "stock_quantity": 0 },
        { "code": "HONCPOT-MD-RAW", "size": "Medium | 360mm X 330mm", "color": "raw", "base_price_rands": 438.5, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Geni Concrete Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "GENCPOT-XL-AMP", "size": "Extra Large | 1300mm x 840mm", "color": "amper", "base_price_rands": 4538.58, "stock_quantity": 0 },
        { "code": "GENCPOT-XL-ANT", "size": "Extra Large | 1300mm x 840mm", "color": "antique rust", "base_price_rands": 4538.58, "stock_quantity": 0 },
        { "code": "GENCPOT-XL-BRO", "size": "Extra Large | 1300mm x 840mm", "color": "bronze", "base_price_rands": 4538.58, "stock_quantity": 0 },
        { "code": "GENCPOT-XL-CHR", "size": "Extra Large | 1300mm x 840mm", "color": "charcoal", "base_price_rands": 4538.58, "stock_quantity": 0 },
        { "code": "GENCPOT-XL-CHR-2", "size": "Extra Large | 1300mm x 840mm", "color": "chryso black", "base_price_rands": 4538.58, "stock_quantity": 0 },
        { "code": "GENCPOT-XL-GRA", "size": "Extra Large | 1300mm x 840mm", "color": "granite", "base_price_rands": 4538.58, "stock_quantity": 0 },
        { "code": "GENCPOT-XL-ROC", "size": "Extra Large | 1300mm x 840mm", "color": "rock", "base_price_rands": 4538.58, "stock_quantity": 0 },
        { "code": "GENCPOT-XL-VEL", "size": "Extra Large | 1300mm x 840mm", "color": "velvet", "base_price_rands": 4538.58, "stock_quantity": 0 },
        { "code": "GENCPOT-XL-RAW", "size": "Extra Large | 1300mm x 840mm", "color": "raw", "base_price_rands": 4538.58, "stock_quantity": 0 },
        { "code": "GENCPOT-LG-AMP", "size": "Large | 1100mm x 710mm", "color": "amper", "base_price_rands": 3282.55, "stock_quantity": 0 },
        { "code": "GENCPOT-LG-ANT", "size": "Large | 1100mm x 710mm", "color": "antique rust", "base_price_rands": 3282.55, "stock_quantity": 0 },
        { "code": "GENCPOT-LG-BRO", "size": "Large | 1100mm x 710mm", "color": "bronze", "base_price_rands": 3282.55, "stock_quantity": 0 },
        { "code": "GENCPOT-LG-CHR", "size": "Large | 1100mm x 710mm", "color": "charcoal", "base_price_rands": 3282.55, "stock_quantity": 0 },
        { "code": "GENCPOT-LG-CHR-2", "size": "Large | 1100mm x 710mm", "color": "chryso black", "base_price_rands": 3282.55, "stock_quantity": 0 },
        { "code": "GENCPOT-LG-GRA", "size": "Large | 1100mm x 710mm", "color": "granite", "base_price_rands": 3282.55, "stock_quantity": 0 },
        { "code": "GENCPOT-LG-ROC", "size": "Large | 1100mm x 710mm", "color": "rock", "base_price_rands": 3282.55, "stock_quantity": 0 },
        { "code": "GENCPOT-LG-VEL", "size": "Large | 1100mm x 710mm", "color": "velvet", "base_price_rands": 3282.55, "stock_quantity": 0 },
        { "code": "GENCPOT-LG-RAW", "size": "Large | 1100mm x 710mm", "color": "raw", "base_price_rands": 3282.55, "stock_quantity": 0 },
        { "code": "GENCPOT-MD-AMP", "size": "Medium | 900mm x 580mm", "color": "amper", "base_price_rands": 1600.82, "stock_quantity": 0 },
        { "code": "GENCPOT-MD-ANT", "size": "Medium | 900mm x 580mm", "color": "antique rust", "base_price_rands": 1600.82, "stock_quantity": 0 },
        { "code": "GENCPOT-MD-BRO", "size": "Medium | 900mm x 580mm", "color": "bronze", "base_price_rands": 1600.82, "stock_quantity": 0 },
        { "code": "GENCPOT-MD-CHR", "size": "Medium | 900mm x 580mm", "color": "charcoal", "base_price_rands": 1600.82, "stock_quantity": 0 },
        { "code": "GENCPOT-MD-CHR-2", "size": "Medium | 900mm x 580mm", "color": "chryso black", "base_price_rands": 1600.82, "stock_quantity": 0 },
        { "code": "GENCPOT-MD-GRA", "size": "Medium | 900mm x 580mm", "color": "granite", "base_price_rands": 1600.82, "stock_quantity": 0 },
        { "code": "GENCPOT-MD-ROC", "size": "Medium | 900mm x 580mm", "color": "rock", "base_price_rands": 1600.82, "stock_quantity": 0 },
        { "code": "GENCPOT-MD-VEL", "size": "Medium | 900mm x 580mm", "color": "velvet", "base_price_rands": 1600.82, "stock_quantity": 0 },
        { "code": "GENCPOT-MD-RAW", "size": "Medium | 900mm x 580mm", "color": "raw", "base_price_rands": 1600.82, "stock_quantity": 0 },
        { "code": "GENCPOT-SM-AMP", "size": "Small | 700mm x 440mm", "color": "amper", "base_price_rands": 1477.68, "stock_quantity": 0 },
        { "code": "GENCPOT-SM-ANT", "size": "Small | 700mm x 440mm", "color": "antique rust", "base_price_rands": 1477.68, "stock_quantity": 0 },
        { "code": "GENCPOT-SM-BRO", "size": "Small | 700mm x 440mm", "color": "bronze", "base_price_rands": 1477.68, "stock_quantity": 0 },
        { "code": "GENCPOT-SM-CHR", "size": "Small | 700mm x 440mm", "color": "charcoal", "base_price_rands": 1477.68, "stock_quantity": 0 },
        { "code": "GENCPOT-SM-CHR-2", "size": "Small | 700mm x 440mm", "color": "chryso black", "base_price_rands": 1477.68, "stock_quantity": 0 },
        { "code": "GENCPOT-SM-GRA", "size": "Small | 700mm x 440mm", "color": "granite", "base_price_rands": 1477.68, "stock_quantity": 0 },
        { "code": "GENCPOT-SM-ROC", "size": "Small | 700mm x 440mm", "color": "rock", "base_price_rands": 1477.68, "stock_quantity": 0 },
        { "code": "GENCPOT-SM-VEL", "size": "Small | 700mm x 440mm", "color": "velvet", "base_price_rands": 1477.68, "stock_quantity": 0 },
        { "code": "GENCPOT-SM-RAW", "size": "Small | 700mm x 440mm", "color": "raw", "base_price_rands": 1477.68, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Funduzi Pot Concrete",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "FUNCPOT-LG-AMP", "size": "Large | 1500mm x 600mm", "color": "amper", "base_price_rands": 2695.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-LG-ANT", "size": "Large | 1500mm x 600mm", "color": "antique rust", "base_price_rands": 2695.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-LG-BRO", "size": "Large | 1500mm x 600mm", "color": "bronze", "base_price_rands": 2695.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-LG-CHR", "size": "Large | 1500mm x 600mm", "color": "charcoal", "base_price_rands": 2695.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-LG-CHR-2", "size": "Large | 1500mm x 600mm", "color": "chryso black", "base_price_rands": 2695.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-LG-GRA", "size": "Large | 1500mm x 600mm", "color": "granite", "base_price_rands": 2695.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-LG-ROC", "size": "Large | 1500mm x 600mm", "color": "rock", "base_price_rands": 2695.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-LG-VEL", "size": "Large | 1500mm x 600mm", "color": "velvet", "base_price_rands": 2695.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-LG-RAW", "size": "Large | 1500mm x 600mm", "color": "raw", "base_price_rands": 2695.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-MD-AMP", "size": "Medium | 1350mm x 570mm", "color": "amper", "base_price_rands": 2295.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-MD-ANT", "size": "Medium | 1350mm x 570mm", "color": "antique rust", "base_price_rands": 2295.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-MD-BRO", "size": "Medium | 1350mm x 570mm", "color": "bronze", "base_price_rands": 2295.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-MD-CHR", "size": "Medium | 1350mm x 570mm", "color": "charcoal", "base_price_rands": 2295.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-MD-CHR-2", "size": "Medium | 1350mm x 570mm", "color": "chryso black", "base_price_rands": 2295.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-MD-GRA", "size": "Medium | 1350mm x 570mm", "color": "granite", "base_price_rands": 2295.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-MD-ROC", "size": "Medium | 1350mm x 570mm", "color": "rock", "base_price_rands": 2295.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-MD-VEL", "size": "Medium | 1350mm x 570mm", "color": "velvet", "base_price_rands": 2295.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-MD-RAW", "size": "Medium | 1350mm x 570mm", "color": "raw", "base_price_rands": 2295.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-SM-AMP", "size": "Small | 1140mm x 500mm", "color": "amper", "base_price_rands": 1699.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-SM-ANT", "size": "Small | 1140mm x 500mm", "color": "antique rust", "base_price_rands": 1699.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-SM-BRO", "size": "Small | 1140mm x 500mm", "color": "bronze", "base_price_rands": 1699.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-SM-CHR", "size": "Small | 1140mm x 500mm", "color": "charcoal", "base_price_rands": 1699.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-SM-CHR-2", "size": "Small | 1140mm x 500mm", "color": "chryso black", "base_price_rands": 1699.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-SM-GRA", "size": "Small | 1140mm x 500mm", "color": "granite", "base_price_rands": 1699.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-SM-ROC", "size": "Small | 1140mm x 500mm", "color": "rock", "base_price_rands": 1699.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-SM-VEL", "size": "Small | 1140mm x 500mm", "color": "velvet", "base_price_rands": 1699.0, "stock_quantity": 0 },
        { "code": "FUNCPOT-SM-RAW", "size": "Small | 1140mm x 500mm", "color": "raw", "base_price_rands": 1699.0, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Fortuna Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "FORCPOT-620-AMP", "size": "620mm x 580mm", "color": "Amper", "base_price_rands": 1139.27, "stock_quantity": 0 },
        { "code": "FORCPOT-620-FWH", "size": "620mm x 580mm", "color": "Flinted White", "base_price_rands": 1139.27, "stock_quantity": 0 },
        { "code": "FORCPOT-620-GRA", "size": "620mm x 580mm", "color": "Granite", "base_price_rands": 1139.27, "stock_quantity": 0 },
        { "code": "FORCPOT-620-GRA-2", "size": "620mm x 580mm", "color": "Granite Sealed", "base_price_rands": 1139.27, "stock_quantity": 0 },
        { "code": "FORCPOT-620-ROC", "size": "620mm x 580mm", "color": "Rock", "base_price_rands": 1139.27, "stock_quantity": 0 },
        { "code": "FORCPOT-620-VEL", "size": "620mm x 580mm", "color": "Velvet", "base_price_rands": 1139.27, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Premium Estantia Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "ESTCPOT-SM-AMP", "size": "Small | 410mm x 280mm", "color": "Amper", "base_price_rands": 377.74, "stock_quantity": 0 },
        { "code": "ESTCPOT-SM-FWH", "size": "Small | 410mm x 280mm", "color": "Flinted White", "base_price_rands": 377.74, "stock_quantity": 0 },
        { "code": "ESTCPOT-SM-GRA", "size": "Small | 410mm x 280mm", "color": "Granite", "base_price_rands": 377.74, "stock_quantity": 0 },
        { "code": "ESTCPOT-SM-GRA-2", "size": "Small | 410mm x 280mm", "color": "Granite Sealed", "base_price_rands": 377.74, "stock_quantity": 0 },
        { "code": "ESTCPOT-SM-ROC", "size": "Small | 410mm x 280mm", "color": "Rock", "base_price_rands": 377.74, "stock_quantity": 0 },
        { "code": "ESTCPOT-SM-VEL", "size": "Small | 410mm x 280mm", "color": "Velvet", "base_price_rands": 377.74, "stock_quantity": 0 },
        { "code": "ESTCPOT-SM-CHR", "size": "Small | 410mm x 280mm", "color": "Chryso Black", "base_price_rands": 377.74, "stock_quantity": 0 },
        { "code": "ESTCPOT-MD-AMP", "size": "Medium | 560mm x 380mm", "color": "Amper", "base_price_rands": 737.89, "stock_quantity": 0 },
        { "code": "ESTCPOT-MD-FWH", "size": "Medium | 560mm x 380mm", "color": "Flinted White", "base_price_rands": 737.89, "stock_quantity": 0 },
        { "code": "ESTCPOT-MD-GRA", "size": "Medium | 560mm x 380mm", "color": "Granite", "base_price_rands": 737.89, "stock_quantity": 0 },
        { "code": "ESTCPOT-MD-GRA-2", "size": "Medium | 560mm x 380mm", "color": "Granite Sealed", "base_price_rands": 737.89, "stock_quantity": 0 },
        { "code": "ESTCPOT-MD-ROC", "size": "Medium | 560mm x 380mm", "color": "Rock", "base_price_rands": 737.89, "stock_quantity": 0 },
        { "code": "ESTCPOT-MD-VEL", "size": "Medium | 560mm x 380mm", "color": "Velvet", "base_price_rands": 737.89, "stock_quantity": 0 },
        { "code": "ESTCPOT-MD-CHR", "size": "Medium | 560mm x 380mm", "color": "Chryso Black", "base_price_rands": 737.89, "stock_quantity": 0 },
        { "code": "ESTCPOT-LG-AMP", "size": "Large | 685mm x 485mm", "color": "Amper", "base_price_rands": 1034.49, "stock_quantity": 0 },
        { "code": "ESTCPOT-LG-FWH", "size": "Large | 685mm x 485mm", "color": "Flinted White", "base_price_rands": 1034.49, "stock_quantity": 0 },
        { "code": "ESTCPOT-LG-GRA", "size": "Large | 685mm x 485mm", "color": "Granite", "base_price_rands": 1034.49, "stock_quantity": 0 },
        { "code": "ESTCPOT-LG-GRA-2", "size": "Large | 685mm x 485mm", "color": "Granite Sealed", "base_price_rands": 1034.49, "stock_quantity": 0 },
        { "code": "ESTCPOT-LG-ROC", "size": "Large | 685mm x 485mm", "color": "Rock", "base_price_rands": 1034.49, "stock_quantity": 0 },
        { "code": "ESTCPOT-LG-VEL", "size": "Large | 685mm x 485mm", "color": "Velvet", "base_price_rands": 1034.49, "stock_quantity": 0 },
        { "code": "ESTCPOT-LG-CHR", "size": "Large | 685mm x 485mm", "color": "Chryso Black", "base_price_rands": 1034.49, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Duo Pair Concrete",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "DUOPAICON-LG-AMP", "size": "Large", "color": "amper", "base_price_rands": 6242.45, "stock_quantity": 0 },
        { "code": "DUOPAICON-LG-ANT", "size": "Large", "color": "antique rust", "base_price_rands": 6242.45, "stock_quantity": 0 },
        { "code": "DUOPAICON-LG-BRO", "size": "Large", "color": "bronze", "base_price_rands": 6242.45, "stock_quantity": 0 },
        { "code": "DUOPAICON-LG-CHR", "size": "Large", "color": "charcoal", "base_price_rands": 6242.45, "stock_quantity": 0 },
        { "code": "DUOPAICON-LG-CHR-2", "size": "Large", "color": "chryso black", "base_price_rands": 6242.45, "stock_quantity": 0 },
        { "code": "DUOPAICON-LG-GRA", "size": "Large", "color": "granite", "base_price_rands": 6242.45, "stock_quantity": 0 },
        { "code": "DUOPAICON-LG-ROC", "size": "Large", "color": "rock", "base_price_rands": 6242.45, "stock_quantity": 0 },
        { "code": "DUOPAICON-LG-VEL", "size": "Large", "color": "velvet", "base_price_rands": 6242.45, "stock_quantity": 0 },
        { "code": "DUOPAICON-LG-RAW", "size": "Large", "color": "raw", "base_price_rands": 6242.45, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Cycad Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "CYCCPOT-970-AMP", "size": "970mm x 540mm", "color": "Amper", "base_price_rands": 2358.62, "stock_quantity": 0 },
        { "code": "CYCCPOT-970-FWH", "size": "970mm x 540mm", "color": "Flinted White", "base_price_rands": 2358.62, "stock_quantity": 0 },
        { "code": "CYCCPOT-970-GRA", "size": "970mm x 540mm", "color": "Granite", "base_price_rands": 2358.62, "stock_quantity": 0 },
        { "code": "CYCCPOT-970-GRA-2", "size": "970mm x 540mm", "color": "Granite Sealed", "base_price_rands": 2358.62, "stock_quantity": 0 },
        { "code": "CYCCPOT-970-ROC", "size": "970mm x 540mm", "color": "Rock", "base_price_rands": 2358.62, "stock_quantity": 0 },
        { "code": "CYCCPOT-970-VEL", "size": "970mm x 540mm", "color": "Velvet", "base_price_rands": 2358.62, "stock_quantity": 0 },
        { "code": "CYCCPOT-970-CHR", "size": "970mm x 540mm", "color": "Chryso Black", "base_price_rands": 2246.3, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Cube Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "CUBCPOT-LG-AMP", "size": "Large | 500mm x 500mm x 500mm", "color": "Amper", "base_price_rands": 1298.26, "stock_quantity": 0 },
        { "code": "CUBCPOT-LG-FWH", "size": "Large | 500mm x 500mm x 500mm", "color": "Flinted White", "base_price_rands": 1298.26, "stock_quantity": 0 },
        { "code": "CUBCPOT-LG-GRA", "size": "Large | 500mm x 500mm x 500mm", "color": "Granite", "base_price_rands": 1298.26, "stock_quantity": 0 },
        { "code": "CUBCPOT-LG-GRA-2", "size": "Large | 500mm x 500mm x 500mm", "color": "Granite Sealed", "base_price_rands": 1298.26, "stock_quantity": 0 },
        { "code": "CUBCPOT-LG-ROC", "size": "Large | 500mm x 500mm x 500mm", "color": "Rock", "base_price_rands": 1298.26, "stock_quantity": 0 },
        { "code": "CUBCPOT-LG-VEL", "size": "Large | 500mm x 500mm x 500mm", "color": "Velvet", "base_price_rands": 1298.26, "stock_quantity": 0 },
        { "code": "CUBCPOT-LG-CHR", "size": "Large | 500mm x 500mm x 500mm", "color": "Chryso Black", "base_price_rands": 1298.26, "stock_quantity": 0 },
        { "code": "CUBCPOT-LG-CHA", "size": "Large | 500mm x 500mm x 500mm", "color": "charcoal light", "base_price_rands": 1298.26, "stock_quantity": 0 },
        { "code": "CUBCPOT-MD-AMP", "size": "Medium | 400mm x 400mm x 400mm", "color": "Amper", "base_price_rands": 914.69, "stock_quantity": 0 },
        { "code": "CUBCPOT-MD-FWH", "size": "Medium | 400mm x 400mm x 400mm", "color": "Flinted White", "base_price_rands": 914.69, "stock_quantity": 0 },
        { "code": "CUBCPOT-MD-GRA", "size": "Medium | 400mm x 400mm x 400mm", "color": "Granite", "base_price_rands": 914.69, "stock_quantity": 0 },
        { "code": "CUBCPOT-MD-GRA-2", "size": "Medium | 400mm x 400mm x 400mm", "color": "Granite Sealed", "base_price_rands": 914.69, "stock_quantity": 0 },
        { "code": "CUBCPOT-MD-ROC", "size": "Medium | 400mm x 400mm x 400mm", "color": "Rock", "base_price_rands": 914.69, "stock_quantity": 0 },
        { "code": "CUBCPOT-MD-VEL", "size": "Medium | 400mm x 400mm x 400mm", "color": "Velvet", "base_price_rands": 914.69, "stock_quantity": 0 },
        { "code": "CUBCPOT-MD-CHR", "size": "Medium | 400mm x 400mm x 400mm", "color": "Chryso Black", "base_price_rands": 914.69, "stock_quantity": 0 },
        { "code": "CUBCPOT-MD-CHA", "size": "Medium | 400mm x 400mm x 400mm", "color": "charcoal light", "base_price_rands": 914.69, "stock_quantity": 0 },
        { "code": "CUBCPOT-SM-AMP", "size": "Small | 300mm x 300mm x 300mm", "color": "Amper", "base_price_rands": 674.05, "stock_quantity": 0 },
        { "code": "CUBCPOT-SM-FWH", "size": "Small | 300mm x 300mm x 300mm", "color": "Flinted White", "base_price_rands": 674.05, "stock_quantity": 0 },
        { "code": "CUBCPOT-SM-GRA", "size": "Small | 300mm x 300mm x 300mm", "color": "Granite", "base_price_rands": 674.05, "stock_quantity": 0 },
        { "code": "CUBCPOT-SM-GRA-2", "size": "Small | 300mm x 300mm x 300mm", "color": "Granite Sealed", "base_price_rands": 674.05, "stock_quantity": 0 },
        { "code": "CUBCPOT-SM-ROC", "size": "Small | 300mm x 300mm x 300mm", "color": "Rock", "base_price_rands": 674.05, "stock_quantity": 0 },
        { "code": "CUBCPOT-SM-VEL", "size": "Small | 300mm x 300mm x 300mm", "color": "Velvet", "base_price_rands": 674.05, "stock_quantity": 0 },
        { "code": "CUBCPOT-SM-CHR", "size": "Small | 300mm x 300mm x 300mm", "color": "Chryso Black", "base_price_rands": 674.05, "stock_quantity": 0 },
        { "code": "CUBCPOT-SM-CHA", "size": "Small | 300mm x 300mm x 300mm", "color": "charcoal light", "base_price_rands": 674.05, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Constantia Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "CONCPOT-MD-AMP", "size": "Medium | 480mm x 620mm", "color": "Amper", "base_price_rands": 1360.41, "stock_quantity": 0 },
        { "code": "CONCPOT-MD-FWH", "size": "Medium | 480mm x 620mm", "color": "Flinted White", "base_price_rands": 1360.41, "stock_quantity": 0 },
        { "code": "CONCPOT-MD-GRA", "size": "Medium | 480mm x 620mm", "color": "Granite", "base_price_rands": 1360.41, "stock_quantity": 0 },
        { "code": "CONCPOT-MD-GRA-2", "size": "Medium | 480mm x 620mm", "color": "Granite Sealed", "base_price_rands": 1360.41, "stock_quantity": 0 },
        { "code": "CONCPOT-MD-ROC", "size": "Medium | 480mm x 620mm", "color": "Rock", "base_price_rands": 1360.41, "stock_quantity": 0 },
        { "code": "CONCPOT-MD-VEL", "size": "Medium | 480mm x 620mm", "color": "Velvet", "base_price_rands": 1360.41, "stock_quantity": 0 },
        { "code": "CONCPOT-SM-AMP", "size": "Small | 330mm x 470mm", "color": "Amper", "base_price_rands": 723.76, "stock_quantity": 0 },
        { "code": "CONCPOT-SM-FWH", "size": "Small | 330mm x 470mm", "color": "Flinted White", "base_price_rands": 723.76, "stock_quantity": 0 },
        { "code": "CONCPOT-SM-GRA", "size": "Small | 330mm x 470mm", "color": "Granite", "base_price_rands": 723.76, "stock_quantity": 0 },
        { "code": "CONCPOT-SM-GRA-2", "size": "Small | 330mm x 470mm", "color": "Granite Sealed", "base_price_rands": 723.76, "stock_quantity": 0 },
        { "code": "CONCPOT-SM-ROC", "size": "Small | 330mm x 470mm", "color": "Rock", "base_price_rands": 723.76, "stock_quantity": 0 },
        { "code": "CONCPOT-SM-VEL", "size": "Small | 330mm x 470mm", "color": "Velvet", "base_price_rands": 723.76, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Premium Clermont Trough Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "CLETRCPOT-SM-AMP", "size": "Small | 270mm h x 310mm w x 600mm l", "color": "Amper", "base_price_rands": 809.21, "stock_quantity": 0 },
        { "code": "CLETRCPOT-SM-FWH", "size": "Small | 270mm h x 310mm w x 600mm l", "color": "Flinted White", "base_price_rands": 809.21, "stock_quantity": 0 },
        { "code": "CLETRCPOT-SM-GRA", "size": "Small | 270mm h x 310mm w x 600mm l", "color": "Granite", "base_price_rands": 809.21, "stock_quantity": 0 },
        { "code": "CLETRCPOT-SM-GRA-2", "size": "Small | 270mm h x 310mm w x 600mm l", "color": "Granite Sealed", "base_price_rands": 809.21, "stock_quantity": 0 },
        { "code": "CLETRCPOT-SM-ROC", "size": "Small | 270mm h x 310mm w x 600mm l", "color": "Rock", "base_price_rands": 809.21, "stock_quantity": 0 },
        { "code": "CLETRCPOT-SM-VEL", "size": "Small | 270mm h x 310mm w x 600mm l", "color": "Velvet", "base_price_rands": 809.21, "stock_quantity": 0 },
        { "code": "CLETRCPOT-SM-CHR", "size": "Small | 270mm h x 310mm w x 600mm l", "color": "Chryso Black", "base_price_rands": 699.0, "stock_quantity": 0 },
        { "code": "CLETRCPOT-LG-AMP", "size": "Large | 270mm h x 310mm w x 1010mm l", "color": "Amper", "base_price_rands": 1087.14, "stock_quantity": 0 },
        { "code": "CLETRCPOT-LG-FWH", "size": "Large | 270mm h x 310mm w x 1010mm l", "color": "Flinted White", "base_price_rands": 1087.14, "stock_quantity": 0 },
        { "code": "CLETRCPOT-LG-GRA", "size": "Large | 270mm h x 310mm w x 1010mm l", "color": "Granite", "base_price_rands": 1087.14, "stock_quantity": 0 },
        { "code": "CLETRCPOT-LG-GRA-2", "size": "Large | 270mm h x 310mm w x 1010mm l", "color": "Granite Sealed", "base_price_rands": 1087.14, "stock_quantity": 0 },
        { "code": "CLETRCPOT-LG-ROC", "size": "Large | 270mm h x 310mm w x 1010mm l", "color": "Rock", "base_price_rands": 1087.14, "stock_quantity": 0 },
        { "code": "CLETRCPOT-LG-VEL", "size": "Large | 270mm h x 310mm w x 1010mm l", "color": "Velvet", "base_price_rands": 1087.14, "stock_quantity": 0 },
        { "code": "CLETRCPOT-LG-CHR", "size": "Large | 270mm h x 310mm w x 1010mm l", "color": "Chryso Black", "base_price_rands": 699.0, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Cedric Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "CEDCPOT-SM-AMP", "size": "Small", "color": "Amper", "base_price_rands": 53.23, "stock_quantity": 0 },
        { "code": "CEDCPOT-SM-FWH", "size": "Small", "color": "Flinted White", "base_price_rands": 53.23, "stock_quantity": 0 },
        { "code": "CEDCPOT-SM-GRA", "size": "Small", "color": "Granite", "base_price_rands": 53.23, "stock_quantity": 0 },
        { "code": "CEDCPOT-SM-GRA-2", "size": "Small", "color": "Granite Sealed", "base_price_rands": 53.23, "stock_quantity": 0 },
        { "code": "CEDCPOT-SM-ROC", "size": "Small", "color": "Rock", "base_price_rands": 53.23, "stock_quantity": 0 },
        { "code": "CEDCPOT-SM-VEL", "size": "Small", "color": "Velvet", "base_price_rands": 53.23, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Carrington Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "CARCPOT-LG-AMP", "size": "Large | 600mm x 590mm", "color": "Amper", "base_price_rands": 2216.54, "stock_quantity": 0 },
        { "code": "CARCPOT-LG-FWH", "size": "Large | 600mm x 590mm", "color": "Flinted White", "base_price_rands": 2216.54, "stock_quantity": 0 },
        { "code": "CARCPOT-LG-GRA", "size": "Large | 600mm x 590mm", "color": "Granite", "base_price_rands": 2216.54, "stock_quantity": 0 },
        { "code": "CARCPOT-LG-GRA-2", "size": "Large | 600mm x 590mm", "color": "Granite Sealed", "base_price_rands": 2216.54, "stock_quantity": 0 },
        { "code": "CARCPOT-LG-ROC", "size": "Large | 600mm x 590mm", "color": "Rock", "base_price_rands": 2216.54, "stock_quantity": 0 },
        { "code": "CARCPOT-LG-VEL", "size": "Large | 600mm x 590mm", "color": "Velvet", "base_price_rands": 2216.54, "stock_quantity": 0 },
        { "code": "CARCPOT-LG-CHR", "size": "Large | 600mm x 590mm", "color": "Chryso Black", "base_price_rands": 2216.54, "stock_quantity": 0 },
        { "code": "CARCPOT-MD-AMP", "size": "Medium | 490mm x 435mm", "color": "Amper", "base_price_rands": 1287.67, "stock_quantity": 0 },
        { "code": "CARCPOT-MD-FWH", "size": "Medium | 490mm x 435mm", "color": "Flinted White", "base_price_rands": 1287.67, "stock_quantity": 0 },
        { "code": "CARCPOT-MD-GRA", "size": "Medium | 490mm x 435mm", "color": "Granite", "base_price_rands": 1287.67, "stock_quantity": 0 },
        { "code": "CARCPOT-MD-GRA-2", "size": "Medium | 490mm x 435mm", "color": "Granite Sealed", "base_price_rands": 1287.67, "stock_quantity": 0 },
        { "code": "CARCPOT-MD-ROC", "size": "Medium | 490mm x 435mm", "color": "Rock", "base_price_rands": 1287.67, "stock_quantity": 0 },
        { "code": "CARCPOT-MD-VEL", "size": "Medium | 490mm x 435mm", "color": "Velvet", "base_price_rands": 1287.67, "stock_quantity": 0 },
        { "code": "CARCPOT-MD-CHR", "size": "Medium | 490mm x 435mm", "color": "Chryso Black", "base_price_rands": 1287.67, "stock_quantity": 0 },
        { "code": "CARCPOT-SM-AMP", "size": "Small | 380mm x 325mm", "color": "Amper", "base_price_rands": 777.54, "stock_quantity": 0 },
        { "code": "CARCPOT-SM-FWH", "size": "Small | 380mm x 325mm", "color": "Flinted White", "base_price_rands": 777.54, "stock_quantity": 0 },
        { "code": "CARCPOT-SM-GRA", "size": "Small | 380mm x 325mm", "color": "Granite", "base_price_rands": 777.54, "stock_quantity": 0 },
        { "code": "CARCPOT-SM-GRA-2", "size": "Small | 380mm x 325mm", "color": "Granite Sealed", "base_price_rands": 777.54, "stock_quantity": 0 },
        { "code": "CARCPOT-SM-ROC", "size": "Small | 380mm x 325mm", "color": "Rock", "base_price_rands": 777.54, "stock_quantity": 0 },
        { "code": "CARCPOT-SM-VEL", "size": "Small | 380mm x 325mm", "color": "Velvet", "base_price_rands": 777.54, "stock_quantity": 0 },
        { "code": "CARCPOT-SM-CHR", "size": "Small | 380mm x 325mm", "color": "Chryso Black", "base_price_rands": 777.54, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Carmen Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "CARCPOT-570-AMP", "size": "570mm x 580mm", "color": "Amper", "base_price_rands": 861.98, "stock_quantity": 0 },
        { "code": "CARCPOT-570-FWH", "size": "570mm x 580mm", "color": "Flinted White", "base_price_rands": 861.98, "stock_quantity": 0 },
        { "code": "CARCPOT-570-GRA", "size": "570mm x 580mm", "color": "Granite", "base_price_rands": 861.98, "stock_quantity": 0 },
        { "code": "CARCPOT-570-GRA-2", "size": "570mm x 580mm", "color": "Granite Sealed", "base_price_rands": 861.98, "stock_quantity": 0 },
        { "code": "CARCPOT-570-ROC", "size": "570mm x 580mm", "color": "Rock", "base_price_rands": 861.98, "stock_quantity": 0 },
        { "code": "CARCPOT-570-VEL", "size": "570mm x 580mm", "color": "Velvet", "base_price_rands": 861.98, "stock_quantity": 0 },
        { "code": "CARCPOT-570-CHR", "size": "570mm x 580mm", "color": "Chryso Black", "base_price_rands": 861.98, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Bolivia Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "BOLCPOT-SM-AMP", "size": "Small | 290MMX290MM", "color": "amper", "base_price_rands": 402.37, "stock_quantity": 0 },
        { "code": "BOLCPOT-SM-ANT", "size": "Small | 290MMX290MM", "color": "antique rust", "base_price_rands": 402.37, "stock_quantity": 0 },
        { "code": "BOLCPOT-SM-BRO", "size": "Small | 290MMX290MM", "color": "bronze", "base_price_rands": 402.37, "stock_quantity": 0 },
        { "code": "BOLCPOT-SM-CHR", "size": "Small | 290MMX290MM", "color": "charcoal", "base_price_rands": 402.37, "stock_quantity": 0 },
        { "code": "BOLCPOT-SM-CHR-2", "size": "Small | 290MMX290MM", "color": "chryso black", "base_price_rands": 402.37, "stock_quantity": 0 },
        { "code": "BOLCPOT-SM-GRA", "size": "Small | 290MMX290MM", "color": "granite", "base_price_rands": 402.37, "stock_quantity": 0 },
        { "code": "BOLCPOT-SM-ROC", "size": "Small | 290MMX290MM", "color": "rock", "base_price_rands": 402.37, "stock_quantity": 0 },
        { "code": "BOLCPOT-SM-VEL", "size": "Small | 290MMX290MM", "color": "velvet", "base_price_rands": 402.37, "stock_quantity": 0 },
        { "code": "BOLCPOT-SM-RAW", "size": "Small | 290MMX290MM", "color": "raw", "base_price_rands": 402.37, "stock_quantity": 0 },
        { "code": "BOLCPOT-MD-AMP", "size": "Medium | 370MMX370MM", "color": "amper", "base_price_rands": 667.56, "stock_quantity": 0 },
        { "code": "BOLCPOT-MD-ANT", "size": "Medium | 370MMX370MM", "color": "antique rust", "base_price_rands": 667.56, "stock_quantity": 0 },
        { "code": "BOLCPOT-MD-BRO", "size": "Medium | 370MMX370MM", "color": "bronze", "base_price_rands": 667.56, "stock_quantity": 0 },
        { "code": "BOLCPOT-MD-CHR", "size": "Medium | 370MMX370MM", "color": "charcoal", "base_price_rands": 667.56, "stock_quantity": 0 },
        { "code": "BOLCPOT-MD-CHR-2", "size": "Medium | 370MMX370MM", "color": "chryso black", "base_price_rands": 667.56, "stock_quantity": 0 },
        { "code": "BOLCPOT-MD-GRA", "size": "Medium | 370MMX370MM", "color": "granite", "base_price_rands": 667.56, "stock_quantity": 0 },
        { "code": "BOLCPOT-MD-ROC", "size": "Medium | 370MMX370MM", "color": "rock", "base_price_rands": 667.56, "stock_quantity": 0 },
        { "code": "BOLCPOT-MD-VEL", "size": "Medium | 370MMX370MM", "color": "velvet", "base_price_rands": 667.56, "stock_quantity": 0 },
        { "code": "BOLCPOT-MD-RAW", "size": "Medium | 370MMX370MM", "color": "raw", "base_price_rands": 667.56, "stock_quantity": 0 },
        { "code": "BOLCPOT-LG-AMP", "size": "Large | 470mm x 480mm", "color": "amper", "base_price_rands": 1026.42, "stock_quantity": 0 },
        { "code": "BOLCPOT-LG-ANT", "size": "Large | 470mm x 480mm", "color": "antique rust", "base_price_rands": 1026.42, "stock_quantity": 0 },
        { "code": "BOLCPOT-LG-BRO", "size": "Large | 470mm x 480mm", "color": "bronze", "base_price_rands": 1026.42, "stock_quantity": 0 },
        { "code": "BOLCPOT-LG-CHR", "size": "Large | 470mm x 480mm", "color": "charcoal", "base_price_rands": 1026.42, "stock_quantity": 0 },
        { "code": "BOLCPOT-LG-CHR-2", "size": "Large | 470mm x 480mm", "color": "chryso black", "base_price_rands": 1026.42, "stock_quantity": 0 },
        { "code": "BOLCPOT-LG-GRA", "size": "Large | 470mm x 480mm", "color": "granite", "base_price_rands": 1026.42, "stock_quantity": 0 },
        { "code": "BOLCPOT-LG-ROC", "size": "Large | 470mm x 480mm", "color": "rock", "base_price_rands": 1026.42, "stock_quantity": 0 },
        { "code": "BOLCPOT-LG-VEL", "size": "Large | 470mm x 480mm", "color": "velvet", "base_price_rands": 1026.42, "stock_quantity": 0 },
        { "code": "BOLCPOT-LG-RAW", "size": "Large | 470mm x 480mm", "color": "raw", "base_price_rands": 1026.42, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Baobab Concrete Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "BOACPOT-LG-AMP", "size": "Large | 800MM X 850MM", "color": "Amper", "base_price_rands": 4098.8, "stock_quantity": 0 },
        { "code": "BOACPOT-LG-FWH", "size": "Large | 800MM X 850MM", "color": "Flinted White", "base_price_rands": 4098.8, "stock_quantity": 0 },
        { "code": "BOACPOT-LG-GRA", "size": "Large | 800MM X 850MM", "color": "Granite", "base_price_rands": 4098.8, "stock_quantity": 0 },
        { "code": "BOACPOT-LG-GRA-2", "size": "Large | 800MM X 850MM", "color": "Granite Sealed", "base_price_rands": 4098.8, "stock_quantity": 0 },
        { "code": "BOACPOT-LG-ROC", "size": "Large | 800MM X 850MM", "color": "Rock", "base_price_rands": 4098.8, "stock_quantity": 0 },
        { "code": "BOACPOT-LG-VEL", "size": "Large | 800MM X 850MM", "color": "Velvet", "base_price_rands": 4098.8, "stock_quantity": 0 },
        { "code": "BOACPOT-LG-CHR", "size": "Large | 800MM X 850MM", "color": "Chryso Black", "base_price_rands": 4098.8, "stock_quantity": 0 },
        { "code": "BOACPOT-MD-AMP", "size": "Medium | 610MM X 300MM", "color": "Amper", "base_price_rands": 2557.79, "stock_quantity": 0 },
        { "code": "BOACPOT-MD-FWH", "size": "Medium | 610MM X 300MM", "color": "Flinted White", "base_price_rands": 2557.79, "stock_quantity": 0 },
        { "code": "BOACPOT-MD-GRA", "size": "Medium | 610MM X 300MM", "color": "Granite", "base_price_rands": 2557.79, "stock_quantity": 0 },
        { "code": "BOACPOT-MD-GRA-2", "size": "Medium | 610MM X 300MM", "color": "Granite Sealed", "base_price_rands": 2557.79, "stock_quantity": 0 },
        { "code": "BOACPOT-MD-ROC", "size": "Medium | 610MM X 300MM", "color": "Rock", "base_price_rands": 2557.79, "stock_quantity": 0 },
        { "code": "BOACPOT-MD-VEL", "size": "Medium | 610MM X 300MM", "color": "Velvet", "base_price_rands": 2557.79, "stock_quantity": 0 },
        { "code": "BOACPOT-MD-CHR", "size": "Medium | 610MM X 300MM", "color": "Chryso Black", "base_price_rands": 2557.79, "stock_quantity": 0 },
        { "code": "BOACPOT-SM-AMP", "size": "Small | 410MM X 430MM", "color": "Amper", "base_price_rands": 1484.89, "stock_quantity": 0 },
        { "code": "BOACPOT-SM-FWH", "size": "Small | 410MM X 430MM", "color": "Flinted White", "base_price_rands": 1484.89, "stock_quantity": 0 },
        { "code": "BOACPOT-SM-GRA", "size": "Small | 410MM X 430MM", "color": "Granite", "base_price_rands": 1484.89, "stock_quantity": 0 },
        { "code": "BOACPOT-SM-GRA-2", "size": "Small | 410MM X 430MM", "color": "Granite Sealed", "base_price_rands": 1484.89, "stock_quantity": 0 },
        { "code": "BOACPOT-SM-ROC", "size": "Small | 410MM X 430MM", "color": "Rock", "base_price_rands": 1484.89, "stock_quantity": 0 },
        { "code": "BOACPOT-SM-VEL", "size": "Small | 410MM X 430MM", "color": "Velvet", "base_price_rands": 1484.89, "stock_quantity": 0 },
        { "code": "BOACPOT-SM-CHR", "size": "Small | 410MM X 430MM", "color": "Chryso Black", "base_price_rands": 1484.89, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Aztec Plant pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "AZTCPOT-LG-AMP", "size": "Large | 1200mm x 420mm", "color": "Amper", "base_price_rands": 2659.8, "stock_quantity": 0 },
        { "code": "AZTCPOT-LG-FWH", "size": "Large | 1200mm x 420mm", "color": "Flinted White", "base_price_rands": 2659.8, "stock_quantity": 0 },
        { "code": "AZTCPOT-LG-GRA", "size": "Large | 1200mm x 420mm", "color": "Granite", "base_price_rands": 2659.8, "stock_quantity": 0 },
        { "code": "AZTCPOT-LG-GRA-2", "size": "Large | 1200mm x 420mm", "color": "Granite Sealed", "base_price_rands": 2659.8, "stock_quantity": 0 },
        { "code": "AZTCPOT-LG-ROC", "size": "Large | 1200mm x 420mm", "color": "Rock", "base_price_rands": 2659.8, "stock_quantity": 0 },
        { "code": "AZTCPOT-LG-VEL", "size": "Large | 1200mm x 420mm", "color": "Velvet", "base_price_rands": 2659.8, "stock_quantity": 0 },
        { "code": "AZTCPOT-LG-CHR", "size": "Large | 1200mm x 420mm", "color": "Chryso Black", "base_price_rands": 2659.8, "stock_quantity": 0 },
        { "code": "AZTCPOT-XL-AMP", "size": "Extra Large | 1400mm X 500mm", "color": "Amper", "base_price_rands": 3465.53, "stock_quantity": 0 },
        { "code": "AZTCPOT-XL-FWH", "size": "Extra Large | 1400mm X 500mm", "color": "Flinted White", "base_price_rands": 3465.53, "stock_quantity": 0 },
        { "code": "AZTCPOT-XL-GRA", "size": "Extra Large | 1400mm X 500mm", "color": "Granite", "base_price_rands": 3465.53, "stock_quantity": 0 },
        { "code": "AZTCPOT-XL-GRA-2", "size": "Extra Large | 1400mm X 500mm", "color": "Granite Sealed", "base_price_rands": 3465.53, "stock_quantity": 0 },
        { "code": "AZTCPOT-XL-ROC", "size": "Extra Large | 1400mm X 500mm", "color": "Rock", "base_price_rands": 3465.53, "stock_quantity": 0 },
        { "code": "AZTCPOT-XL-VEL", "size": "Extra Large | 1400mm X 500mm", "color": "Velvet", "base_price_rands": 3465.53, "stock_quantity": 0 },
        { "code": "AZTCPOT-XL-CHR", "size": "Extra Large | 1400mm X 500mm", "color": "Chryso Black", "base_price_rands": 3465.53, "stock_quantity": 0 },
        { "code": "AZTCPOT-MD-AMP", "size": "Medium | 1000mm x 350mm", "color": "Amper", "base_price_rands": 1864.71, "stock_quantity": 0 },
        { "code": "AZTCPOT-MD-FWH", "size": "Medium | 1000mm x 350mm", "color": "Flinted White", "base_price_rands": 1864.71, "stock_quantity": 0 },
        { "code": "AZTCPOT-MD-GRA", "size": "Medium | 1000mm x 350mm", "color": "Granite", "base_price_rands": 1864.71, "stock_quantity": 0 },
        { "code": "AZTCPOT-MD-GRA-2", "size": "Medium | 1000mm x 350mm", "color": "Granite Sealed", "base_price_rands": 1864.71, "stock_quantity": 0 },
        { "code": "AZTCPOT-MD-ROC", "size": "Medium | 1000mm x 350mm", "color": "Rock", "base_price_rands": 1864.71, "stock_quantity": 0 },
        { "code": "AZTCPOT-MD-VEL", "size": "Medium | 1000mm x 350mm", "color": "Velvet", "base_price_rands": 1864.71, "stock_quantity": 0 },
        { "code": "AZTCPOT-MD-CHR", "size": "Medium | 1000mm x 350mm", "color": "Chryso Black", "base_price_rands": 1864.71, "stock_quantity": 0 },
        { "code": "AZTCPOT-SM-AMP", "size": "Small | 800mm X 290mm", "color": "Amper", "base_price_rands": 1284.18, "stock_quantity": 0 },
        { "code": "AZTCPOT-SM-FWH", "size": "Small | 800mm X 290mm", "color": "Flinted White", "base_price_rands": 1284.18, "stock_quantity": 0 },
        { "code": "AZTCPOT-SM-GRA", "size": "Small | 800mm X 290mm", "color": "Granite", "base_price_rands": 1284.18, "stock_quantity": 0 },
        { "code": "AZTCPOT-SM-GRA-2", "size": "Small | 800mm X 290mm", "color": "Granite Sealed", "base_price_rands": 1284.18, "stock_quantity": 0 },
        { "code": "AZTCPOT-SM-ROC", "size": "Small | 800mm X 290mm", "color": "Rock", "base_price_rands": 1284.18, "stock_quantity": 0 },
        { "code": "AZTCPOT-SM-VEL", "size": "Small | 800mm X 290mm", "color": "Velvet", "base_price_rands": 1284.18, "stock_quantity": 0 },
        { "code": "AZTCPOT-SM-CHR", "size": "Small | 800mm X 290mm", "color": "Chryso Black", "base_price_rands": 1284.18, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Rum Plant pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "RUMCPOT-SM-AMP", "size": "Small", "color": "Amper", "base_price_rands": 485.0, "stock_quantity": 0 },
        { "code": "RUMCPOT-SM-GRD", "size": "Small", "color": "Granite dark", "base_price_rands": 485.0, "stock_quantity": 0 },
        { "code": "RUMCPOT-SM-ROC", "size": "Small", "color": "Rock", "base_price_rands": 485.0, "stock_quantity": 0 },
        { "code": "RUMCPOT-SM-VEL", "size": "Small", "color": "Velvet", "base_price_rands": 485.0, "stock_quantity": 0 },
        { "code": "RUMCPOT-SM-CHR", "size": "Small", "color": "Chryso Black", "base_price_rands": 485.0, "stock_quantity": 0 },
        { "code": "RUMCPOT-SM-ROL", "size": "Small", "color": "Rolled white", "base_price_rands": 485.0, "stock_quantity": 0 },
        { "code": "RUMCPOT-MD-GRD", "size": "Medium", "color": "Granite dark", "base_price_rands": 720.0, "stock_quantity": 0 },
        { "code": "RUMCPOT-MD-ROC", "size": "Medium", "color": "Rock", "base_price_rands": 720.0, "stock_quantity": 0 },
        { "code": "RUMCPOT-MD-VEL", "size": "Medium", "color": "Velvet", "base_price_rands": 720.0, "stock_quantity": 0 },
        { "code": "RUMCPOT-MD-CHR", "size": "Medium", "color": "Chryso Black", "base_price_rands": 720.0, "stock_quantity": 0 },
        { "code": "RUMCPOT-MD-FWH", "size": "Medium", "color": "Flinted White", "base_price_rands": 720.0, "stock_quantity": 0 },
        { "code": "RUMCPOT-MD-ROL", "size": "Medium", "color": "Rolled white", "base_price_rands": 720.0, "stock_quantity": 0 },
        { "code": "RUMCPOT-LG-GRD", "size": "Large", "color": "Granite dark", "base_price_rands": 2170.15, "stock_quantity": 0 },
        { "code": "RUMCPOT-LG-ROC", "size": "Large", "color": "Rock", "base_price_rands": 2170.15, "stock_quantity": 0 },
        { "code": "RUMCPOT-LG-VEL", "size": "Large", "color": "Velvet", "base_price_rands": 2170.15, "stock_quantity": 0 },
        { "code": "RUMCPOT-LG-CHR", "size": "Large", "color": "Chryso Black", "base_price_rands": 2170.15, "stock_quantity": 0 },
        { "code": "RUMCPOT-LG-GRL", "size": "Large", "color": "Granite light", "base_price_rands": 2170.15, "stock_quantity": 0 },
        { "code": "RUMCPOT-LG-ROL", "size": "Large", "color": "Rolled white", "base_price_rands": 2170.15, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Premium Arizona Plant pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "ARICPOT-SM-AMP", "size": "Small | 720mm L x 530mm W x 510mm H", "color": "Amper", "base_price_rands": 1326.4, "stock_quantity": 0 },
        { "code": "ARICPOT-SM-FWH", "size": "Small | 720mm L x 530mm W x 510mm H", "color": "Flinted White", "base_price_rands": 1326.4, "stock_quantity": 0 },
        { "code": "ARICPOT-SM-GRL", "size": "Small | 720mm L x 530mm W x 510mm H", "color": "Granite light", "base_price_rands": 1326.4, "stock_quantity": 0 },
        { "code": "ARICPOT-SM-GRA", "size": "Small | 720mm L x 530mm W x 510mm H", "color": "Granite dark sealed", "base_price_rands": 1326.4, "stock_quantity": 0 },
        { "code": "ARICPOT-SM-ROC", "size": "Small | 720mm L x 530mm W x 510mm H", "color": "Rock", "base_price_rands": 1326.4, "stock_quantity": 0 },
        { "code": "ARICPOT-SM-VEL", "size": "Small | 720mm L x 530mm W x 510mm H", "color": "Velvet", "base_price_rands": 1326.4, "stock_quantity": 0 },
        { "code": "ARICPOT-LG-AMP", "size": "Large | 1140mm L x 660mm W x 640mm H", "color": "Amper", "base_price_rands": 2677.42, "stock_quantity": 0 },
        { "code": "ARICPOT-LG-FWH", "size": "Large | 1140mm L x 660mm W x 640mm H", "color": "Flinted White", "base_price_rands": 2677.42, "stock_quantity": 0 },
        { "code": "ARICPOT-LG-GRL", "size": "Large | 1140mm L x 660mm W x 640mm H", "color": "Granite light", "base_price_rands": 2677.42, "stock_quantity": 0 },
        { "code": "ARICPOT-LG-GRA", "size": "Large | 1140mm L x 660mm W x 640mm H", "color": "Granite dark sealed", "base_price_rands": 2677.42, "stock_quantity": 0 },
        { "code": "ARICPOT-LG-ROC", "size": "Large | 1140mm L x 660mm W x 640mm H", "color": "Rock", "base_price_rands": 2677.42, "stock_quantity": 0 },
        { "code": "ARICPOT-LG-VEL", "size": "Large | 1140mm L x 660mm W x 640mm H", "color": "Velvet", "base_price_rands": 2677.42, "stock_quantity": 0 }
      ]
    },
    {
      "name": "Amazon Plant Pot",
      "category": "Concrete Pot",
      "description_html": "",
      "skus": [
        { "code": "AMACPOT-LG-AMP", "size": "Large | 1700mm x 600mm", "color": "Amper", "base_price_rands": 4425.98, "stock_quantity": 0 },
        { "code": "AMACPOT-LG-FWH", "size": "Large | 1700mm x 600mm", "color": "Flinted White", "base_price_rands": 4425.98, "stock_quantity": 0 },
        { "code": "AMACPOT-LG-GRA", "size": "Large | 1700mm x 600mm", "color": "Granite", "base_price_rands": 4425.98, "stock_quantity": 0 },
        { "code": "AMACPOT-LG-GRA-2", "size": "Large | 1700mm x 600mm", "color": "Granite Sealed", "base_price_rands": 4425.98, "stock_quantity": 0 },
        { "code": "AMACPOT-LG-ROC", "size": "Large | 1700mm x 600mm", "color": "Rock", "base_price_rands": 4425.98, "stock_quantity": 0 },
        { "code": "AMACPOT-LG-VEL", "size": "Large | 1700mm x 600mm", "color": "Velvet", "base_price_rands": 4425.98, "stock_quantity": 0 },
        { "code": "AMACPOT-LG-CHR", "size": "Large | 1700mm x 600mm", "color": "Chryso Black", "base_price_rands": 4425.98, "stock_quantity": 0 },
        { "code": "AMACPOT-MD-AMP", "size": "Medium | 1355mm x 500mm", "color": "Amper", "base_price_rands": 2930.72, "stock_quantity": 0 },
        { "code": "AMACPOT-MD-FWH", "size": "Medium | 1355mm x 500mm", "color": "Flinted White", "base_price_rands": 2930.72, "stock_quantity": 0 },
        { "code": "AMACPOT-MD-GRA", "size": "Medium | 1355mm x 500mm", "color": "Granite", "base_price_rands": 2930.72, "stock_quantity": 0 },
        { "code": "AMACPOT-MD-GRA-2", "size": "Medium | 1355mm x 500mm", "color": "Granite Sealed", "base_price_rands": 2930.72, "stock_quantity": 0 },
        { "code": "AMACPOT-MD-ROC", "size": "Medium | 1355mm x 500mm", "color": "Rock", "base_price_rands": 2930.72, "stock_quantity": 0 },
        { "code": "AMACPOT-MD-VEL", "size": "Medium | 1355mm x 500mm", "color": "Velvet", "base_price_rands": 2930.72, "stock_quantity": 0 },
        { "code": "AMACPOT-MD-CHR", "size": "Medium | 1355mm x 500mm", "color": "Chryso Black", "base_price_rands": 2930.72, "stock_quantity": 0 },
        { "code": "AMACPOT-SM-AMP", "size": "Small | 1030mm x 440mm", "color": "Amper", "base_price_rands": 2251.71, "stock_quantity": 0 },
        { "code": "AMACPOT-SM-FWH", "size": "Small | 1030mm x 440mm", "color": "Flinted White", "base_price_rands": 2251.71, "stock_quantity": 0 },
        { "code": "AMACPOT-SM-GRA", "size": "Small | 1030mm x 440mm", "color": "Granite", "base_price_rands": 2251.71, "stock_quantity": 0 },
        { "code": "AMACPOT-SM-GRA-2", "size": "Small | 1030mm x 440mm", "color": "Granite Sealed", "base_price_rands": 2251.71, "stock_quantity": 0 },
        { "code": "AMACPOT-SM-ROC", "size": "Small | 1030mm x 440mm", "color": "Rock", "base_price_rands": 2251.71, "stock_quantity": 0 },
        { "code": "AMACPOT-SM-VEL", "size": "Small | 1030mm x 440mm", "color": "Velvet", "base_price_rands": 2251.71, "stock_quantity": 0 },
        { "code": "AMACPOT-SM-CHR", "size": "Small | 1030mm x 440mm", "color": "Chryso Black", "base_price_rands": 2251.71, "stock_quantity": 0 }
      ]
    }
  ]
}

def main() -> None:
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if not admin:
            print("Admin user not found. Run seed_admin first.")
            return

        store_service = StoreService(db)
        sales_service = SalesAgentService(db)
        team_service = DeliveryTeamService(db)
        product_service = ProductService(db)

        stores = [
            StoreCreate(
                name="Pot and Planter - Church Street",
                code="POT-JHB-CHURCH",
                store_type="nursery",
                address="279 Church Street, Johannesburg North, Randburg",
                phone="+27 72 812 5073 / +27 82 331 9171",
                email="hellojhb@thepotandplanter.co.za",
            ),
            StoreCreate(
                name="Pot and Planter - Cornubia Mall",
                code="POT-KZN-CORNUBIA",
                store_type="nursery",
                address="Corner of Flanders Drive & Tacoma Drive, Blackburn Estate, Mount Edgecombe",
                phone="+27 71 140 1608",
                email="hellokzn@thepotandplanter.co.za",
            ),
            StoreCreate(
                name="Pot and Planter - Table Bay Mall",
                code="POT-CPT-TABLEBAY",
                store_type="nursery",
                address="In the underground parking, by the gravel area in the back",
                phone="+27 66 345 1098",
                email="hellocpt@thepotandplanter.co.za",
            ),
            StoreCreate(
                name="Pot and Planter - Cedar",
                code="POT-JHB-CEDAR",
                store_type="nursery",
                address="Cnr Cedar & Frederick Road, Broadacres",
                phone="+27 71 140 1608",
                email="hellojhb@thepotandplanter.co.za",
            ),
            StoreCreate(
                name="PotShack Online Store",
                code="SHOP-ONLINE",
                store_type="shopify",
            ),
        ]

        for store in stores:
            try:
                created = store_service.create_store(store, admin.id)
                print(f"Created store: {created.code}")
            except Exception:
                existing = db.query(Store).filter(Store.code == store.code).first()
                if not existing:
                    raise
                store_service.update_store(
                    existing.id,
                    StoreUpdate(
                        name=store.name,
                        store_type=store.store_type,
                        address=store.address,
                        phone=store.phone,
                        email=store.email,
                        is_active=True,
                    ),
                    admin.id,
                )
                print(f"Updated store: {store.code}")

        try:
            sales_service.create_agent(
                SalesAgentCreate(name="Sue Elmira", code="4500", phone="082 4644 376"),
                admin.id,
            )
            print("Created sales agent: Sue Elmira (4500)")
        except Exception:
            existing = db.query(SalesAgent).filter(SalesAgent.code == "4500").first()
            if not existing:
                raise
            sales_service.update_agent(
                existing.id,
                SalesAgentUpdate(name="Sue Elmira", phone="082 4644 376", is_active=True),
                admin.id,
            )
            print("Updated sales agent: Sue Elmira (4500)")

        team_defs = [
            ("D-4501", "Delivery Team Alpha", ["Aiden Driver", "Lea Runner", "Sam Loader"]),
            ("D-4502", "Delivery Team Bravo", ["Nia Driver", "Tariq Runner", "Olivia Loader"]),
            ("D-4503", "Delivery Team Charlie", ["Ben Driver", "Zara Runner", "Mila Loader"]),
        ]
        for code, name, members in team_defs:
            try:
                team = team_service.create_team(DeliveryTeamCreate(name=name, code=code), admin.id)
                print(f"Created delivery team: {code}")
            except Exception:
                team = db.query(DeliveryTeam).filter(DeliveryTeam.code == code).first()
                if not team:
                    raise
                team_service.update_team(team.id, DeliveryTeamUpdate(name=name, is_active=True), admin.id)
                print(f"Updated delivery team: {code}")

            for member_name in members:
                existing_member = (
                    db.query(DeliveryTeamMember)
                    .filter(DeliveryTeamMember.delivery_team_id == team.id, DeliveryTeamMember.name == member_name)
                    .first()
                )
                if existing_member:
                    print(f"  Member exists: {member_name}")
                    continue
                team_service.add_member(team.id, DeliveryTeamMemberCreate(name=member_name), admin.id)
                print(f"  Added member: {member_name}")

        bulk_request = ProductBulkImportRequest(**PRODUCTS_TO_IMPORT)
        products = product_service.import_bulk(bulk_request, admin)
        print(f"Imported products: {len(products)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
