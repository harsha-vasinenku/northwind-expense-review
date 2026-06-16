import { useRef, useState } from "react";
import { UploadCloud, X, FileText } from "lucide-react";
import clsx from "clsx";

interface FileUploaderProps {
  files: File[];
  onFilesChange: (files: File[]) => void;
}

const ACCEPTED = ".pdf,.jpg,.jpeg,.png,.txt";

export function FileUploader({ files, onFilesChange }: FileUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const addFiles = (incoming: FileList | null) => {
    if (!incoming) return;
    const newFiles = Array.from(incoming).filter(
      (f) => !files.some((existing) => existing.name === f.name)
    );
    onFilesChange([...files, ...newFiles]);
  };

  const remove = (name: string) => {
    onFilesChange(files.filter((f) => f.name !== name));
  };

  return (
    <div className="space-y-3">
      <div
        className={clsx(
          "border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors",
          dragOver
            ? "border-blue-400 bg-blue-50"
            : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"
        )}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          addFiles(e.dataTransfer.files);
        }}
        role="button"
        aria-label="Upload receipt files"
        tabIndex={0}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
      >
        <UploadCloud className="w-8 h-8 text-gray-400 mx-auto mb-2" aria-hidden />
        <p className="text-sm text-gray-600">
          Drop files here or <span className="text-blue-600 underline">click to upload</span>
        </p>
        <p className="text-xs text-gray-400 mt-1">Accepts: PDF, JPG, PNG, TXT</p>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED}
          multiple
          className="hidden"
          onChange={(e) => addFiles(e.target.files)}
          aria-label="File input"
        />
      </div>

      {files.length > 0 && (
        <ul className="space-y-1">
          {files.map((f) => (
            <li
              key={f.name}
              className="flex items-center justify-between bg-white border border-gray-200 rounded-lg px-3 py-2"
            >
              <div className="flex items-center gap-2 min-w-0">
                <FileText className="w-4 h-4 text-gray-400 shrink-0" aria-hidden />
                <span className="text-sm text-gray-700 truncate">{f.name}</span>
                <span className="text-xs text-gray-400 shrink-0">
                  ({(f.size / 1024).toFixed(0)} KB)
                </span>
              </div>
              <button
                onClick={() => remove(f.name)}
                className="text-gray-400 hover:text-red-500 ml-2 shrink-0"
                aria-label={`Remove ${f.name}`}
              >
                <X className="w-4 h-4" aria-hidden />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
