import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import {
  poiPreviewUploadApi,
  poiImportConfirmApi,
  poiTemplateDownloadUrl,
  poiValidationReportUrl,
} from "@/api/endpoints";
import type {
  PoiPreviewResponse,
  PoiImportResponse,
} from "@/api/poiDataManagerTypes";

export function usePoiTemplateDownload() {
  return useQuery<Blob>({
    queryKey: ["poi-template"],
    queryFn: async () => {
      const { data } = await api.get<Blob>(poiTemplateDownloadUrl(), {
        responseType: "blob",
      });
      return data;
    },
    enabled: false,
    retry: 0,
  });
}

export function usePoiPreviewUpload() {
  return useMutation<PoiPreviewResponse, Error, File>({
    mutationFn: poiPreviewUploadApi,
  });
}

export function usePoiImportConfirm() {
  return useMutation<PoiImportResponse, Error, string>({
    mutationFn: poiImportConfirmApi,
  });
}

export function usePoiValidationReport(previewId: string | null) {
  return useQuery<Blob>({
    queryKey: ["poi-validation-report", previewId],
    queryFn: async () => {
      const { data } = await api.get<Blob>(
        poiValidationReportUrl(previewId!),
        { responseType: "blob" }
      );
      return data;
    },
    enabled: false,
    retry: 0,
  });
}
