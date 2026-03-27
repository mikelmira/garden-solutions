# Performance Expectations

## 1. Volumetric Assumptions
- **Orders**: ~50 per day.
- **Items per Order**: Average 10, Max 100.
- **Concurrent Users**: ~10 active Sales Agents, 2 Admins.
- **Conclusion**: This is Low Volume. We do not need complex caching layers (Redis) or sharding.

## 2. Response Time Goals
- **API (Online)**: < 300ms for standard reads/writes.
- **Dashboard Load**: < 1.5s (First Contentful Paint).
- **Offline Action**: Immediate (< 50ms) optimistic UI update.

## 3. Sync performance
- **Delay**: It is acceptable for a Sales Agent to sync 5 minutes after visiting a site.
- **Batch Size**: Sync payloads should be chunked if > 50 items (rare in V1).

## 4. Mobile Constraints
- **Devices**: Mid-range Android and iPads.
- **Network**: Edge/3G coverage in remote nurseries.
- **Assets**: Keep JS bundle size small (< 500kb initial load) to facilitate fast initial cache.

## 5. Not Optimised in V1
- **Report Generation**: calculating yearly stats might take 5-10s. Acceptable.
- **Search**: Linear SQL `ILIKE` is acceptable. No ElasticSearch.
