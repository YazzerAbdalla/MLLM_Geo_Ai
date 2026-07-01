import { create } from "zustand";

export type Lang = "en" | "ar";

type Dict = Record<string, { en: string; ar: string }>;

export const dict: Dict = {
  app_title: { en: "Urban AI Dashboard", ar: "لوحة الذكاء الحضري" },
  mock_mode: { en: "MOCK MODE", ar: "وضع تجريبي" },
  area_selection: { en: "Area selection", ar: "اختيار المنطقة" },
  search_place: { en: "Search city (e.g. Cairo)", ar: "ابحث عن مدينة (مثال: القاهرة)" },
  draw_bbox: { en: "Draw bbox (D)", ar: "ارسم مربعًا (D)" },
  load_area: { en: "Load area", ar: "تحميل المنطقة" },
  cells_estimate: { en: "Estimated cells", ar: "عدد الخلايا المقدر" },
  warn_300: { en: "Large area — may be slow", ar: "منطقة كبيرة — قد تكون بطيئة" },
  block_500: { en: "Too large — reduce area or grid size", ar: "كبيرة جدًا — قلل المساحة" },
  grid_config: { en: "Grid configuration", ar: "إعداد الشبكة" },
  grid_size: { en: "Grid size", ar: "حجم الخلية" },
  projection_label: { en: "Projection: EPSG:32636 (metric)", ar: "الإسقاط: EPSG:32636 (متري)" },
  modalities: { en: "Modalities", ar: "الوسائط" },
  modality_poi: { en: "POI", ar: "نقاط الاهتمام" },
  modality_image: { en: "Image", ar: "الصور" },
  modality_graph: { en: "Graph", ar: "الرسم البياني" },
  modality_text: { en: "Text", ar: "النص" },
  ablation_preset: { en: "Ablation preset", ar: "إعداد الاستئصال" },
  preset_custom: { en: "Custom", ar: "مخصص" },
  preset_poi_only: { en: "POI only", ar: "POI فقط" },
  preset_poi_image: { en: "POI + Image", ar: "POI + صور" },
  preset_poi_image_graph: { en: "POI + Image + Graph", ar: "POI + صور + رسم" },
  preset_all: { en: "All modalities", ar: "كل الوسائط" },
  model: { en: "Model", ar: "النموذج" },
  model_mlp: { en: "MLP", ar: "MLP" },
  model_gnn: { en: "GNN (spatial)", ar: "GNN (مكاني)" },
  fusion: { en: "Fusion method", ar: "طريقة الدمج" },
  fusion_concat: { en: "Concatenation", ar: "تجميع" },
  fusion_weighted: { en: "Weighted", ar: "موزون" },
  fusion_attention: { en: "Attention", ar: "انتباه" },
  classify: { en: "Classify (C)", ar: "تصنيف (C)" },
  cancel: { en: "Cancel", ar: "إلغاء" },
  layers: { en: "Layers", ar: "الطبقات" },
  layer_classification: { en: "Classification", ar: "التصنيف" },
  layer_poi: { en: "POI heatmap", ar: "خريطة POI" },
  layer_roads: { en: "Roads", ar: "الطرق" },
  layer_graph: { en: "Graph topology", ar: "هيكل الرسم" },
  layer_satellite: { en: "Satellite", ar: "قمر صناعي" },
  cell_detail: { en: "Cell detail", ar: "تفاصيل الخلية" },
  evaluation: { en: "Evaluation", ar: "التقييم" },
  cell_story: { en: "Cell Story (POI semantic vector)", ar: "قصة الخلية (متجه دلالي POI)" },
  cell_story_sub: { en: "384-dim MLLM embedding (aggregated)", ar: "تضمين MLLM ٣٨٤ بُعدًا (مجمّع)" },
  graph_metrics: { en: "Graph metrics", ar: "مقاييس الرسم" },
  embeddings: { en: "Embedding norms", ar: "معايير التضمين" },
  satellite: { en: "Satellite thumbnail", ar: "صورة قمر صناعي" },
  pin_compare: { en: "Pin to compare", ar: "تثبيت للمقارنة" },
  unpin: { en: "Unpin", ar: "إلغاء التثبيت" },
  loading_step: { en: "Loading", ar: "جارٍ التحميل" },
  step_downloading_poi: { en: "Downloading POI…", ar: "تحميل نقاط الاهتمام…" },
  step_mapping_poi_to_nodes: { en: "Mapping POI → graph nodes…", ar: "ربط POI بعقد الرسم…" },
  step_building_graph: { en: "Building road graph…", ar: "بناء رسم الطرق…" },
  step_classifying: { en: "Classifying cells…", ar: "تصنيف الخلايا…" },
  ground_truth: { en: "Upload ground truth (CSV)", ar: "ارفع البيانات الحقيقية (CSV)" },
  accuracy: { en: "Accuracy", ar: "الدقة" },
  macro_f1: { en: "Macro F1", ar: "Macro F1" },
  weighted_f1: { en: "Weighted F1", ar: "Weighted F1" },
  spatial_accuracy: { en: "Spatial Accuracy", ar: "الدقة المكانية" },
  per_class_f1: { en: "Per-class F1", ar: "F1 لكل صنف" },
  confusion_matrix: { en: "Confusion matrix", ar: "مصفوفة الالتباس" },
  no_classification: { en: "Run classification to see metrics", ar: "شغّل التصنيف لعرض المقاييس" },
  distribution: { en: "Distribution", ar: "التوزيع" },
  avg_confidence: { en: "Avg confidence", ar: "متوسط الثقة" },
  nav_dashboard: { en: "Dashboard", ar: "لوحة" },
  nav_mllm: { en: "MLLM Builder", ar: "منشئ MLLM" },
  nav_twin: { en: "Digital Twin", ar: "التوأم الرقمي" },
  nav_training: { en: "Training Lab", ar: "مختبر التدريب" },
  nav_ablation: { en: "Ablation", ar: "الاستئصال" },
  coming_v2: { en: "Coming in v2", ar: "قريبًا في الإصدار 2" },
  back_to_dashboard: { en: "Back to dashboard", ar: "العودة إلى اللوحة" },
  draw_area: { en: "Draw area", ar: "ارسم منطقة" },
  drawing_mode: { en: "Drawing mode — click & drag on the map", ar: "وضع الرسم — اسحب على الخريطة" },
  clear_area: { en: "Clear area", ar: "مسح المنطقة" },
  custom_area_active: { en: "Custom area active", ar: "منطقة مخصصة نشطة" },
  open_full_details: { en: "Open full details", ar: "افتح التفاصيل الكاملة" },
  grid_details: { en: "Grid details", ar: "تفاصيل الخلية" },
  dominant_class: { en: "Dominant class", ar: "الفئة المهيمنة" },
  confidence: { en: "Confidence", ar: "الثقة" },
  pois_in_cell: { en: "POIs in cell", ar: "النقاط داخل الخلية" },
  show_roads: { en: "Show roads", ar: "عرض الطرق" },
  cell_not_found: { en: "Cell not found", ar: "الخلية غير موجودة" },
  loading: { en: "Loading…", ar: "جارٍ التحميل…" },
  res: { en: "Residential", ar: "سكني" },
  com: { en: "Commercial", ar: "تجاري" },
  ind: { en: "Industrial", ar: "صناعي" },
  vector_breakdown: { en: "224-dim vector: POI 64 · Image 64 · Graph 32 · Text 64", ar: "متجه ٢٢٤ بُعدًا: POI ٦٤ · صور ٦٤ · رسم ٣٢ · نص ٦٤" },
  thumbnail_empty: { en: "No satellite thumbnail available", ar: "لا توجد صورة قمر صناعي" },
  cell_details_title: { en: "Cell Details", ar: "تفاصيل الخلية" },
  cell_pois_title: { en: "Cell POIs", ar: "نقاط الاهتمام في الخلية" },
  poi_count: { en: "POI count", ar: "عدد نقاط الاهتمام" },
  poi_categories: { en: "POI categories", ar: "فئات نقاط الاهتمام" },
  no_pois_in_cell: { en: "No POIs found inside this cell", ar: "لا توجد نقاط اهتمام داخل هذه الخلية" },
  load_pois_error: { en: "Failed to load POI data", ar: "فشل تحميل بيانات نقاط الاهتمام" },
  retry: { en: "Retry", ar: "إعادة المحاولة" },
  back_to_classification: { en: "Back to Classification", ar: "العودة إلى التصنيف" },
  cell_not_found_in_result: { en: "Cell not found in classification result", ar: "الخلية غير موجودة في نتيجة التصنيف" },
  nav_poi_heatmap: { en: "POI Heatmap", ar: "خريطة POI" },
  internal_poi_heatmap_title: { en: "POI Heatmap", ar: "خريطة POI" },
  internal_poi_heatmap_badge: { en: "Internal", ar: "داخلي" },
  internal_poi_heatmap_stat_total: { en: "Total POIs", ar: "إجمالي POI" },
  internal_poi_heatmap_stat_categories: { en: "Categories", ar: "الفئات" },
  internal_poi_heatmap_stat_source: { en: "Dataset Source", ar: "مصدر البيانات" },
  internal_poi_heatmap_stat_zoom: { en: "Current Zoom", ar: "التكبير الحالي" },
  internal_poi_heatmap_stat_coords: { en: "Mouse Coords", ar: "إحداثيات الماوس" },
  internal_poi_heatmap_legend: { en: "Legend", ar: "وسيلة الإيضاح" },
  internal_poi_heatmap_density: { en: "Density", ar: "الكثافة" },
  internal_poi_heatmap_point: { en: "Point (zoom ≥ 15)", ar: "نقطة (تكبير ≥ ١٥)" },
  internal_poi_heatmap_empty: { en: "No POIs were found in the dataset.", ar: "لم يتم العثور على نقاط اهتمام في مجموعة البيانات." },
  internal_poi_heatmap_error: { en: "Failed to load POI dataset.", ar: "فشل تحميل مجموعة بيانات POI." },
  internal_poi_heatmap_statistics: { en: "Statistics", ar: "الإحصائيات" },

  spatial_accuracy_tooltip: { en: "Measures how spatially consistent neighboring predictions are. Computed using KDTree neighborhood analysis.", ar: "يقيس مدى اتساق التوقعات مكانيًا. يتم حسابه باستخدام تحليل الجوار KDTree." },
  spatial_accuracy_detail: { en: "Higher values indicate that neighboring urban cells have consistent predictions.", ar: "تشير القيم الأعلى إلى أن الخلايا الحضرية المجاورة لها توقعات متسقة." },
  overall_higher: { en: "Overall Accuracy is higher — model performs better on label match than spatial consistency.", ar: "الدقة الإجمالية أعلى — أداء النموذج أفضل في مطابقة التسميات من الاتساق المكاني." },
  spatial_higher: { en: "Spatial Accuracy is higher — predictions are more spatially coherent than label-accurate.", ar: "الدقة المكانية أعلى — التوقعات أكثر اتساقًا مكانيًا من دقة التسميات." },
  accuracy_equal: { en: "Both metrics are equal — label accuracy and spatial consistency are balanced.", ar: "كلا المقياسين متساويان — دقة التسمية والاتساق المكاني متوازنان." },

  poi_analysis_title: { en: "POI Analysis", ar: "تحليل نقاط الاهتمام" },
  poi_analysis_draw_rect: { en: "Rectangle", ar: "مستطيل" },
  poi_analysis_draw_polygon: { en: "Polygon", ar: "مضلع" },
  poi_analysis_edit: { en: "Edit", ar: "تعديل" },
  poi_analysis_delete: { en: "Delete", ar: "حذف" },
  poi_analysis_zoom_selection: { en: "Zoom to Selection", ar: "تكبير للتحديد" },
  poi_analysis_area: { en: "Area (km²)", ar: "المساحة (كم²)" },
  poi_analysis_perimeter: { en: "Perimeter (km)", ar: "المحيط (كم)" },
  poi_analysis_center: { en: "Center Coords", ar: "إحداثيات المركز" },
  poi_analysis_export: { en: "Export JSON", ar: "تصدير JSON" },
  poi_analysis_search_placeholder: { en: "Search by name, category, or type…", ar: "ابحث بالاسم أو الفئة أو النوع…" },
  poi_analysis_all_categories: { en: "All Categories", ar: "جميع الفئات" },
  poi_analysis_summary_area: { en: "Area Name", ar: "اسم المنطقة" },
  poi_analysis_summary_pois: { en: "POIs", ar: "نقاط الاهتمام" },
  poi_analysis_summary_density: { en: "Density", ar: "الكثافة" },
  poi_analysis_summary_dominant: { en: "Dominant", ar: "السائد" },
  poi_analysis_draw_hint_rect: { en: "Click & drag to draw rectangle", ar: "انقر واسحب لرسم مستطيل" },
  poi_analysis_draw_hint_polygon: { en: "Click to place vertices, double-click to finish", ar: "انقر لوضع النقاط، انقر مرتين للإنهاء" },
};

// POI Data Manager keys (after poi_analysis_draw_hint_polygon)
dict.poi_manager_wizard_title = { en: "POI Data Manager", ar: "مدير بيانات نقاط الاهتمام" };
dict.poi_manager_step_download = { en: "Download Template", ar: "تنزيل القالب" };
dict.poi_manager_step_upload = { en: "Upload CSV", ar: "رفع CSV" };
dict.poi_manager_step_validate = { en: "Validation", ar: "التحقق" };
dict.poi_manager_step_preview = { en: "Preview", ar: "معاينة" };
dict.poi_manager_step_import = { en: "Import", ar: "استيراد" };
dict.poi_manager_step_next = { en: "Continue", ar: "متابعة" };
dict.poi_manager_download_template = { en: "Download Template", ar: "تنزيل القالب" };
dict.poi_manager_upload_csv = { en: "Upload CSV", ar: "رفع CSV" };
dict.poi_manager_reset = { en: "Reset", ar: "إعادة تعيين" };
dict.poi_manager_preview_badge = { en: "Preview", ar: "معاينة" };
dict.poi_manager_empty_title = { en: "Import POI Data", ar: "استيراد بيانات نقاط الاهتمام" };
dict.poi_manager_empty_desc = { en: "Upload a CSV file to add new POIs to the project.", ar: "ارفع ملف CSV لإضافة نقاط اهتمام جديدة إلى المشروع." };
dict.poi_manager_drag_zone = { en: "Drag & drop CSV file here", ar: "اسحب ملف CSV هنا" };
dict.poi_manager_uploading = { en: "Uploading…", ar: "جارٍ الرفع…" };
dict.poi_manager_upload_progress = { en: "{percent}% uploaded", ar: "تم رفع {percent}%" };
dict.poi_manager_valid_pct = { en: "Valid", ar: "صالح" };
dict.poi_manager_warnings = { en: "Warnings", ar: "تحذيرات" };
dict.poi_manager_errors = { en: "Errors", ar: "أخطاء" };
dict.poi_manager_duplicate_coords = { en: "Duplicate Coordinates", ar: "إحداثيات مكررة" };
dict.poi_manager_duplicate_pois = { en: "Duplicate POIs", ar: "نقاط اهتمام مكررة" };
dict.poi_manager_validation_detail = { en: "View Details", ar: "عرض التفاصيل" };
dict.poi_manager_validation_hide = { en: "Hide Details", ar: "إخفاء التفاصيل" };
dict.poi_manager_summary_uploaded = { en: "Rows Uploaded", ar: "الصفوف المرفوعة" };
dict.poi_manager_summary_valid = { en: "Rows Valid", ar: "الصفوف الصالحة" };
dict.poi_manager_summary_skipped = { en: "Rows Skipped", ar: "الصفوف المتخطاة" };
dict.poi_manager_summary_categories = { en: "Unique Categories", ar: "الفئات الفريدة" };
dict.poi_manager_summary_center = { en: "Center", ar: "المركز" };
dict.poi_manager_summary_bbox = { en: "Bounding Box", ar: "المربع المحيط" };
dict.poi_manager_sidebar_title = { en: "Uploaded POIs", ar: "نقاط الاهتمام المرفوعة" };
dict.poi_manager_filter_all = { en: "All", ar: "الكل" };
dict.poi_manager_filter_new = { en: "New", ar: "جديد" };
dict.poi_manager_filter_duplicate_poi = { en: "Duplicate POIs", ar: "نقاط مكررة" };
dict.poi_manager_filter_duplicate_coord = { en: "Duplicate Coords", ar: "إحداثيات مكررة" };
dict.poi_manager_filter_warnings = { en: "Warnings", ar: "تحذيرات" };
dict.poi_manager_filter_errors = { en: "Errors", ar: "أخطاء" };
dict.poi_manager_search_placeholder_v2 = { en: "Search by name, category, address, or type…", ar: "ابحث بالاسم أو الفئة أو العنوان أو النوع…" };
dict.poi_manager_category_health = { en: "Health", ar: "صحة" };
dict.poi_manager_category_education = { en: "Education", ar: "تعليم" };
dict.poi_manager_category_retail = { en: "Retail", ar: "تجزئة" };
dict.poi_manager_category_food = { en: "Food", ar: "طعام" };
dict.poi_manager_category_religious = { en: "Religious", ar: "ديني" };
dict.poi_manager_category_government = { en: "Government", ar: "حكومي" };
dict.poi_manager_category_transport = { en: "Transport", ar: "نقل" };
dict.poi_manager_confirm_title = { en: "Ready to Import", ar: "جاهز للاستيراد" };
dict.poi_manager_confirm_new = { en: "{count} new POIs", ar: "{count} نقاط جديدة" };
dict.poi_manager_confirm_proceed = { en: "Proceed", ar: "متابعة" };
dict.poi_manager_success_title = { en: "Import Successful", ar: "تم الاستيراد بنجاح" };
dict.poi_manager_success_imported = { en: "Imported", ar: "تم الاستيراد" };
dict.poi_manager_success_duplicate_pois = { en: "Duplicate POIs", ar: "نقاط مكررة" };
dict.poi_manager_success_duplicate_coords = { en: "Duplicate Coordinates", ar: "إحداثيات مكررة" };
dict.poi_manager_success_time = { en: "Processing Time", ar: "وقت المعالجة" };
dict.poi_manager_success_go_dashboard = { en: "Go to Dashboard", ar: "الذهاب إلى لوحة التحكم" };
dict.poi_manager_success_stay = { en: "Stay Here", ar: "البقاء هنا" };
dict.poi_manager_success_import_another = { en: "Import Another File", ar: "استيراد ملف آخر" };
dict.poi_manager_success_redirecting = { en: "Redirecting to Dashboard…", ar: "جارٍ التوجيه إلى لوحة التحكم…" };
dict.poi_manager_quality_title = { en: "AI Data Quality Review", ar: "مراجعة جودة البيانات بالذكاء الاصطناعي" };
dict.poi_manager_quality_score = { en: "Overall quality", ar: "الجودة الإجمالية" };
dict.poi_manager_quality_findings = { en: "Findings", ar: "النتائج" };
dict.poi_manager_quality_suggestions = { en: "Suggestions", ar: "الاقتراحات" };
dict.poi_manager_quality_fix = { en: "Fix with AI", ar: "إصلاح بالذكاء الاصطناعي" };
dict.poi_manager_quality_fixing = { en: "Applying AI fixes…", ar: "جارٍ تطبيق الإصلاحات…" };
dict.poi_manager_quality_loading = { en: "Analyzing data quality…", ar: "جارٍ تحليل جودة البيانات…" };
dict.poi_manager_upload_error = { en: "Failed to upload CSV", ar: "فشل رفع CSV" };
dict.poi_manager_import_error = { en: "Failed to import POI data", ar: "فشل استيراد بيانات POI" };
dict.poi_manager_unsaved_title = { en: "Unsaved Changes", ar: "تغييرات غير محفوظة" };
dict.poi_manager_unsaved_desc = { en: "You have unsaved preview data. Discard changes?", ar: "لديك بيانات معاينة غير محفوظة. هل تريد تجاهل التغييرات؟" };
dict.poi_manager_discard = { en: "Discard", ar: "تجاهل" };
dict.poi_manager_stay_page = { en: "Stay", ar: "البقاء" };
dict.poi_manager_importing = { en: "Importing POI data…", ar: "جارٍ استيراد بيانات POI…" };
dict.poi_manager_no_preview = { en: "No Preview Available", ar: "لا توجد معاينة متاحة" };
dict.poi_manager_all_deleted = { en: "All POIs have been removed", ar: "تمت إزالة جميع نقاط الاهتمام" };
dict.poi_manager_delete_poi = { en: "Remove", ar: "إزالة" };
dict.poi_manager_no_valid_pois = { en: "No valid POIs available for preview.", ar: "لا توجد نقاط اهتمام صالحة للمعاينة." };
dict.nav_poi_manager = { en: "POI Manager", ar: "مدير نقاط الاهتمام" };
dict.no_results = { en: "No results", ar: "لا توجد نتائج" };
dict.ai_query = { en: "AI Query Assistant", ar: "مساعد الاستعلام AI" };
dict.ai_query_placeholder = { en: "e.g. Show commercial areas", ar: "مثال: عرض المناطق التجارية" };
dict.ai_query_search = { en: "Search", ar: "بحث" };
dict.ai_query_searching = { en: "Searching...", ar: "جارٍ البحث..." };
dict.ai_query_found = { en: "Found {n} matching {n, plural, one {cell} other {cells}}", ar: "تم العثور على {n} خلية {n, plural, one {} other {}} مطابقة" };
dict.ai_query_avg_confidence = { en: "Average Confidence", ar: "متوسط الثقة" };
dict.ai_query_top_categories = { en: "Top Categories", ar: "أهم الفئات" };
dict.ai_query_matched_cells = { en: "Matched Cells", ar: "الخلايا المطابقة" };
dict.ai_query_no_results = { en: "No matching locations were found.", ar: "لم يتم العثور على مواقع مطابقة." };
dict.ai_query_error = { en: "Failed to query. Please try again.", ar: "فشل الاستعلام. يرجى المحاولة مرة أخرى." };
dict.ai_query_history = { en: "Recent Searches", ar: "عمليات البحث الأخيرة" };
dict.ai_query_cell = { en: "Cell", ar: "خلية" };

interface I18nState {
  lang: Lang;
  setLang: (l: Lang) => void;
}

export const useI18nStore = create<I18nState>((set) => ({
  lang: (typeof window !== "undefined" && (localStorage.getItem("lang") as Lang)) || "en",
  setLang: (l) => {
    localStorage.setItem("lang", l);
    document.documentElement.setAttribute("lang", l);
    document.documentElement.setAttribute("dir", l === "ar" ? "rtl" : "ltr");
    set({ lang: l });
  },
}));

export function useI18n() {
  const lang = useI18nStore((s) => s.lang);
  const setLang = useI18nStore((s) => s.setLang);
  const t = (key: keyof typeof dict) => dict[key]?.[lang] ?? String(key);
  return { t, lang, setLang };
}

/** Initialize <html dir/lang> on first import */
if (typeof window !== "undefined") {
  const l = useI18nStore.getState().lang;
  document.documentElement.setAttribute("lang", l);
  document.documentElement.setAttribute("dir", l === "ar" ? "rtl" : "ltr");
}