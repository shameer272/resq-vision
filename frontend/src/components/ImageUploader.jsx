import React, { useRef } from "react";
import { UploadCloud, Camera, X, Image as ImageIcon, Plus } from "lucide-react";
import { useLanguage } from "../context/LanguageContext";

export default function ImageUploader({ selectedFiles, setSelectedFiles, previews, setPreviews }) {
  const { t } = useLanguage();
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    addFiles(files);
  };

  const addFiles = (files) => {
    const validFormats = ["image/jpeg", "image/png", "image/webp"];
    const maxFiles = 4;
    const remainingSlots = maxFiles - selectedFiles.length;

    if (remainingSlots <= 0) {
      alert(t("uploader.err_max_files", "Maximum 4 images allowed for multimodal scene fusion."));
      return;
    }

    const filtered = files.filter((f) => {
      if (!validFormats.includes(f.type)) {
        alert(`File ${f.name} ` + t("uploader.err_invalid_type", "is not a valid JPEG/PNG/WebP image."));
        return false;
      }
      if (f.size > 10 * 1024 * 1024) {
        alert(`File ${f.name} ` + t("uploader.err_size_limit", "exceeds maximum allowed size of 10MB."));
        return false;
      }
      return true;
    }).slice(0, remainingSlots);

    const newFiles = [...selectedFiles, ...filtered];
    setSelectedFiles(newFiles);

    // Create previews
    const newPreviews = filtered.map((file) => ({
      file,
      url: URL.createObjectURL(file),
      name: file.name,
      size: (file.size / (1024 * 1024)).toFixed(2) + " MB",
    }));
    setPreviews([...previews, ...newPreviews]);
  };

  const removeFile = (index) => {
    const updatedFiles = selectedFiles.filter((_, i) => i !== index);
    const updatedPreviews = previews.filter((_, i) => {
      if (i === index) {
        URL.revokeObjectURL(previews[i].url);
        return false;
      }
      return true;
    });
    setSelectedFiles(updatedFiles);
    setPreviews(updatedPreviews);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  return (
    <div className="w-full">
      {/* Hidden file inputs */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        multiple
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
      />
      <input
        type="file"
        ref={cameraInputRef}
        onChange={handleFileChange}
        capture="environment"
        accept="image/*"
        className="hidden"
      />

      {/* Dropzone */}
      {selectedFiles.length === 0 ? (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => fileInputRef.current?.click()}
          className="group relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-700 bg-slate-900/40 p-8 text-center transition-all hover:border-red-500/80 hover:bg-slate-900/80 cursor-pointer"
        >
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-800 text-slate-400 group-hover:text-red-400 group-hover:bg-slate-800/80 transition-colors shadow-inner">
            <UploadCloud className="h-7 w-7" />
          </div>
          <h3 className="mt-3 text-sm font-semibold text-slate-200">
            {t("uploader.title", "Upload Scene Imagery (Up to 4 Images)")}
          </h3>
          <p className="mt-1 text-xs text-slate-400 max-w-sm">
            {t("uploader.desc", "Drag & drop emergency photographs, browse your files, or capture with camera.")}
          </p>
          <p className="mt-2 text-[11px] text-slate-500">
            {t("uploader.limits", "Supports JPEG, PNG, WebP (Max 10MB each)")}
          </p>

          <div className="mt-4 flex items-center space-x-3">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                fileInputRef.current?.click();
              }}
              className="flex items-center space-x-1.5 rounded-lg bg-slate-800 border border-slate-700 px-3.5 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 hover:text-white"
            >
              <ImageIcon className="h-3.5 w-3.5 text-slate-400" />
              <span>{t("uploader.btn_browse", "Browse Files")}</span>
            </button>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                cameraInputRef.current?.click();
              }}
              className="flex items-center space-x-1.5 rounded-lg bg-red-600/20 border border-red-500/50 px-3.5 py-1.5 text-xs font-medium text-red-300 hover:bg-red-600/30"
            >
              <Camera className="h-3.5 w-3.5 text-red-400" />
              <span>{t("uploader.btn_camera", "Capture Camera")}</span>
            </button>
          </div>
        </div>
      ) : (
        <div>
          {/* Thumbnails grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {previews.map((item, index) => (
              <div
                key={index}
                className="group relative aspect-4/3 rounded-lg overflow-hidden border border-slate-700 bg-slate-900 shadow-md"
              >
                <img
                  src={item.url}
                  alt={`Incident View ${index + 1}`}
                  className="h-full w-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent opacity-90" />
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className="absolute top-1.5 right-1.5 flex h-6 w-6 items-center justify-center rounded-full bg-slate-950/90 text-slate-300 hover:bg-red-600 hover:text-white transition-colors"
                  title="Remove image"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
                <div className="absolute bottom-1.5 left-2 right-2 text-[10px] text-slate-300 truncate">
                  <span className="font-semibold text-white">{t("uploader.view_prefix", "View")} {index + 1}:</span> {item.size}
                </div>
              </div>
            ))}

            {/* Add more button if < 4 */}
            {selectedFiles.length < 4 && (
              <div
                onClick={() => fileInputRef.current?.click()}
                className="flex flex-col items-center justify-center aspect-4/3 rounded-lg border-2 border-dashed border-slate-800 bg-slate-900/30 hover:bg-slate-900/60 hover:border-slate-700 cursor-pointer transition-all text-slate-400 hover:text-slate-200"
              >
                <Plus className="h-6 w-6 mb-1 text-slate-500" />
                <span className="text-[11px] font-medium">{t("uploader.add_view", "Add View")} ({selectedFiles.length}/4)</span>
              </div>
            )}
          </div>

          <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-400">
            <span>
              {selectedFiles.length} {t("uploader.selected_count", "of 4 images selected for multi-perspective Gemma 4 analysis")}
            </span>
            <button
              type="button"
              onClick={() => {
                setSelectedFiles([]);
                setPreviews([]);
              }}
              className="text-red-400 hover:text-red-300 underline"
            >
              {t("uploader.btn_clear_all", "Clear All")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

