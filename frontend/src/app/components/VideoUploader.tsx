import { useState, useRef, useCallback } from 'react';
import { Upload, X, Video, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface VideoUploaderProps {
  onVideoUpload: (file: File) => void;
  uploadedVideo: File | null;
}

export function VideoUploader({ onVideoUpload, uploadedVideo }: VideoUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('video/')) {
        simulateUpload(file);
      }
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('video/')) {
        simulateUpload(file);
      }
    }
  }, []);

  const simulateUpload = (file: File) => {
    setIsUploading(true);
    setUploadProgress(0);

    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsUploading(false);
          onVideoUpload(file);
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };

  const handleRemove = () => {
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    onVideoUpload(null as any);
  };

  return (
    <div className="w-full">
      <input
        ref={fileInputRef}
        type="file"
        accept="video/*"
        onChange={handleFileSelect}
        className="hidden"
      />

      <AnimatePresence mode="wait">
        {!uploadedVideo ? (
          <motion.div
            key="upload-area"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => !isUploading && fileInputRef.current?.click()}
            className={`
              relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
              transition-all duration-200
              ${isDragging 
                ? 'border-[var(--primary-500)] bg-[var(--primary-50)]' 
                : 'border-[var(--gray-200)] bg-white hover:border-[var(--primary-500)] hover:bg-[var(--gray-50)]'
              }
              ${isUploading ? 'pointer-events-none opacity-70' : ''}
            `}
          >
            <div className="flex flex-col items-center gap-4">
              <div className={`
                w-16 h-16 rounded-full flex items-center justify-center
                ${isDragging ? 'bg-[var(--primary-500)]' : 'bg-[var(--gray-100)]'}
                transition-colors duration-200
              `}>
                {isUploading ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  >
                    <Upload className={isDragging ? 'text-white' : 'text-[var(--gray-600)]'} size={32} />
                  </motion.div>
                ) : (
                  <Upload className={isDragging ? 'text-white' : 'text-[var(--gray-600)]'} size={32} />
                )}
              </div>

              {isUploading ? (
                <div className="w-full max-w-xs">
                  <div className="text-sm mb-2" style={{ color: 'var(--gray-600)' }}>
                    上传中... {uploadProgress}%
                  </div>
                  <div className="w-full h-2 bg-[var(--gray-200)] rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-[var(--primary-500)]"
                      initial={{ width: 0 }}
                      animate={{ width: `${uploadProgress}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                </div>
              ) : (
                <>
                  <div>
                    <p className="text-base mb-1" style={{ color: 'var(--gray-900)' }}>
                      {isDragging ? '放开以上传视频' : '拖拽视频文件到此处'}
                    </p>
                    <p className="text-sm" style={{ color: 'var(--gray-400)' }}>
                      或点击选择文件
                    </p>
                  </div>
                  <div className="flex gap-2 text-xs" style={{ color: 'var(--gray-400)' }}>
                    <span>支持格式: MP4, MOV, AVI</span>
                    <span>•</span>
                    <span>最大 500MB</span>
                  </div>
                </>
              )}
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="uploaded-preview"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="relative border-2 border-[var(--gray-200)] rounded-xl p-6 bg-white"
          >
            <button
              onClick={handleRemove}
              className="absolute top-4 right-4 w-8 h-8 rounded-full bg-[var(--error)] text-white flex items-center justify-center hover:bg-[var(--error)]/90 transition-colors"
            >
              <X size={18} />
            </button>

            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-[var(--success)]/10 flex items-center justify-center">
                <CheckCircle2 className="text-[var(--success)]" size={24} />
              </div>
              
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Video className="text-[var(--gray-600)]" size={18} />
                  <span className="text-sm" style={{ color: 'var(--gray-900)' }}>
                    {uploadedVideo.name}
                  </span>
                </div>
                <p className="text-xs" style={{ color: 'var(--gray-400)' }}>
                  {(uploadedVideo.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>

              <div className="text-xs px-3 py-1 rounded-full" style={{ backgroundColor: 'var(--success)', color: 'white' }}>
                上传成功
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
