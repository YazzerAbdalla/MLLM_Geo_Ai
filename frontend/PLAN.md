# Route-Driven Architecture + Cell POI Workflow

## Architecture

```
/  (workspace — full Sidebar)
  → User configures & runs classification
  → On completion → navigate to /classification/{jobId}
  ↓
/classification/:jobId  (review mode — slim sidebar)
  → Reads jobId from URL
  → Fetches classification via useClassification(jobId)
  → Map + RightPanel + simplified Sidebar (layers only)
  → Click cell → sidebar shows detail
  → Double-click → navigate to POI page
  ↓
/classification/:jobId/cell/:cellId  (cell detail page)
  → Route-driven, survives refresh
  ↓
/classification/:jobId/grid/:gridId/cell/:cellId/pois  (cell POI page)
  → Route-driven, Turf spatial filter, survives refresh
```

## Routes (order-sensitive)

| Route | Component | Mode |
|---|---|---|
| `/` | Index | Workspace (full Sidebar) |
| `/classification/:jobId/grid/:gridId/cell/:cellId/pois` | CellPoisPage | Full page |
| `/classification/:jobId/cell/:cellId` | CellDetailsPage | Full page |
| `/classification/:jobId` | Index | Review (slim Sidebar) |
| `/grid/:id/details` | GridDetails (unchanged) | Legacy |
| `*` | NotFound | — |

## Files

### Create
1. `src/lib/gridUtils.ts` — `extractGridIdFromThumbnail`, `buildThumbnailUrl`
2. `src/hooks/api/useClassification.ts` — React Query hook
3. `src/hooks/api/useCell.ts` — derived hook
4. `src/hooks/api/usePois.ts` — React Query hook
5. `src/pages/CellDetailsPage.tsx` — cell detail page
6. `src/pages/CellPoisPage.tsx` — cell POI page

### Modify
7. `src/lib/api/types.ts` — add `gridId` to `CellDatum`
8. `src/api/types.ts` — add `PoiItem`
9. `src/api/endpoints.ts` — add `gridPoisApi`
10. `src/lib/adapters.ts` — extract gridId in `featureToCell`
11. `src/App.tsx` — add routes (specific before generic)
12. `src/pages/Index.tsx` — accept optional `:jobId` route param
13. `src/components/dashboard/MapView.tsx` — props `jobId`, `gridId`, `cells`; double-click
14. `src/components/dashboard/Sidebar.tsx` — optional review mode
15. `src/components/dashboard/CellDetailPanel.tsx` — robust thumbnail
16. `src/lib/i18n.ts` — new keys

## Key Design Decisions

- **MapView is fully prop-driven**: receives `jobId`, `gridId`, `cells` as props — no store reads for data
- **Index page dual-mode**: workspace (`/`) shows full config Sidebar; review (`/classification/:jobId`) shows slim layers-only Sidebar
- **Detail pages are pure route-driven**: no Zustand dependency, all data via React Query from URL params
- **gridId extracted in adapter**: `featureToCell` extracts gridId from `satellite_thumbnail_url` and stores it on `CellDatum.gridId`
- **Turf packages**: only `@turf/boolean-point-in-polygon` + `@turf/helpers` (not the full bundle)

## Implementation Order

1. Install dependencies
2. Create utility + types + endpoints
3. Create React Query hooks
4. Update routing + Index page
5. Update MapView + Sidebar
6. Update CellDetailPanel thumbnail
7. Create CellDetailsPage
8. Create CellPoisPage
9. Update i18n
10. Build & lint verification
