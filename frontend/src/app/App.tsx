import { useState, useEffect } from 'react';
import { VideoUploader } from './components/VideoUploader';
import { InstructionInput } from './components/InstructionInput';
import { ProgressIndicator } from './components/ProgressIndicator';
import { VideoPreview } from './components/VideoPreview';
import { Video, Settings, HelpCircle, Zap, ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { toast, Toaster } from 'sonner';
import { apiService, ProcessStatus } from '../services/api';

interface ProcessStep {
  id: string;
  label: string;
  description: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
}

type AppState = 'upload' | 'processing' | 'result';

export default function App() {
  const [appState, setAppState] = useState<AppState>('upload');
  const [uploadedVideo, setUploadedVideo] = useState<File | null>(null);
  const [instruction, setInstruction] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // 处理状态
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [estimatedTime, setEstimatedTime] = useState(120);
  const [currentIteration, setCurrentIteration] = useState(1);
  const [videoId, setVideoId] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  
  const [steps, setSteps] = useState<ProcessStep[]>([
    { id: '1', label: '视频分析', description: '分析视频内容和场景', status: 'pending' },
    { id: '2', label: '场景识别', description: '识别关键场景和镜头', status: 'pending' },
    { id: '3', label: '智能剪辑', description: '根据指令进行剪辑处理', status: 'pending' },
    { id: '4', label: '特效处理', description: '添加转场和特效', status: 'pending' },
    { id: '5', label: '渲染导出', description: '生成最终视频', status: 'pending' },
  ]);

  const handleStartProcessing = async () => {
    if (!uploadedVideo) {
      toast.error('请先上传视频文件');
      return;
    }
    if (!instruction.trim()) {
      toast.error('请输入编辑指令');
      return;
    }

    try {
      setAppState('processing');
      
      // 1. 上传视频
      toast.info('正在上传视频...');
      const uploadResponse = await apiService.uploadVideo(uploadedVideo);
      setVideoId(uploadResponse.videoId);
      
      // 2. 开始处理
      toast.info('开始处理视频...');
      const processRequest = {
        videoId: uploadResponse.videoId,
        instruction: instruction.trim(),
        quality: '标准质量',
        resolution: '1920x1080',
        keepAudio: true
      };
      
      const processResponse = await apiService.startProcessing(processRequest);
      setTaskId(processResponse.taskId);
      
      // 3. 开始轮询处理状态
      startStatusPolling(uploadResponse.videoId);
      
    } catch (error) {
      console.error('处理失败:', error);
      toast.error(`处理失败: ${error instanceof Error ? error.message : '未知错误'}`);
      setAppState('upload');
    }
  };

  const simulateProcessing = () => {
    let currentProgress = 0;
    let stepIndex = 0;
    
    const updateStepStatus = (index: number, status: 'processing' | 'completed') => {
      setSteps(prev => prev.map((step, i) => 
        i === index ? { ...step, status } : step
      ));
    };

    const interval = setInterval(() => {
      currentProgress += 2;
      setProgress(currentProgress);
      
      // 更新估计时间
      const remaining = Math.max(0, 120 - Math.floor(currentProgress * 1.2));
      setEstimatedTime(remaining);

      // 更新步骤状态
      const newStepIndex = Math.floor((currentProgress / 100) * steps.length);
      if (newStepIndex > stepIndex) {
        updateStepStatus(stepIndex, 'completed');
        stepIndex = newStepIndex;
        if (stepIndex < steps.length) {
          updateStepStatus(stepIndex, 'processing');
          setCurrentStep(stepIndex);
        }
      } else if (stepIndex < steps.length) {
        updateStepStatus(stepIndex, 'processing');
        setCurrentStep(stepIndex);
      }

      if (currentProgress >= 100) {
        clearInterval(interval);
        updateStepStatus(steps.length - 1, 'completed');
        setTimeout(() => {
          setAppState('result');
          toast.success('视频处理完成！');
        }, 500);
      }
    }, 100);
  };

  const startStatusPolling = (videoId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const status = await apiService.getProcessStatus(videoId);
        
        // 更新进度和状态
        setProgress(status.progress);
        setEstimatedTime(status.estimatedTime);
        
        // 更新步骤状态
        const stepIndex = steps.findIndex(step => step.label === status.currentStep);
        if (stepIndex >= 0) {
          setSteps(prev => prev.map((step, i) => {
            if (i < stepIndex) return { ...step, status: 'completed' };
            if (i === stepIndex) return { ...step, status: 'processing' };
            return { ...step, status: 'pending' };
          }));
          setCurrentStep(stepIndex);
        }
        
        // 处理完成
        if (status.status === 'completed' && status.resultUrl) {
          clearInterval(pollInterval);
          setResultUrl(status.resultUrl);
          setAppState('result');
          toast.success('视频处理完成！');
        }
        
        // 处理错误
        if (status.status === 'error') {
          clearInterval(pollInterval);
          toast.error(`处理失败: ${status.error || '未知错误'}`);
          setAppState('upload');
        }
        
      } catch (error) {
        console.error('状态查询失败:', error);
        clearInterval(pollInterval);
        toast.error('状态查询失败，请检查网络连接');
        setAppState('upload');
      }
    }, 2000); // 每2秒查询一次状态
  };

  const handleReset = () => {
    setAppState('upload');
    setUploadedVideo(null);
    setInstruction('');
    setProgress(0);
    setCurrentStep(0);
    setCurrentIteration(1);
    setEstimatedTime(120);
    setVideoId(null);
    setTaskId(null);
    setResultUrl(null);
    setSteps(steps.map(step => ({ ...step, status: 'pending' })));
  };

  const handleDownload = async () => {
    if (!videoId) {
      toast.error('无法下载，视频ID不存在');
      return;
    }
    
    try {
      toast.info('正在下载视频...');
      const blob = await apiService.downloadResult(videoId);
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `edited_video_${videoId}.mp4`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      toast.success('下载完成！');
    } catch (error) {
      console.error('下载失败:', error);
      toast.error(`下载失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--gray-50)]">
      <Toaster position="top-center" richColors />
      
      {/* 导航栏 */}
      <header className="bg-white border-b border-[var(--gray-200)]">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[var(--primary-500)] to-[var(--secondary-500)] flex items-center justify-center">
                <Video className="text-white" size={24} />
              </div>
              <div>
                <h1 className="text-base" style={{ color: 'var(--gray-900)' }}>
                  智能视频编辑代理系统
                </h1>
                <p className="text-xs" style={{ color: 'var(--gray-400)' }}>
                  AI-Powered Video Editing Platform
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <button className="p-2 hover:bg-[var(--gray-100)] rounded-lg transition-colors">
                <HelpCircle size={20} style={{ color: 'var(--gray-600)' }} />
              </button>
              <button className="p-2 hover:bg-[var(--gray-100)] rounded-lg transition-colors">
                <Settings size={20} style={{ color: 'var(--gray-600)' }} />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* 主内容区 */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <AnimatePresence mode="wait">
          {appState === 'upload' && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="grid lg:grid-cols-[1fr_1.2fr] gap-6"
            >
              {/* 左侧：视频上传 */}
              <div className="space-y-6">
                <div className="bg-white rounded-xl border border-[var(--gray-200)] p-6">
                  <h2 className="mb-4">视频上传</h2>
                  <VideoUploader 
                    onVideoUpload={setUploadedVideo}
                    uploadedVideo={uploadedVideo}
                  />
                </div>

                {uploadedVideo && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-white rounded-xl border border-[var(--gray-200)] p-6"
                  >
                    <VideoPreview 
                      title="视频预览"
                      videoUrl={URL.createObjectURL(uploadedVideo)}
                      isOriginal
                    />
                  </motion.div>
                )}
              </div>

              {/* 右侧：编辑指令和控制 */}
              <div className="space-y-6">
                <div className="bg-white rounded-xl border border-[var(--gray-200)] p-6">
                  <h2 className="mb-4">编辑指令</h2>
                  <InstructionInput
                    instruction={instruction}
                    onInstructionChange={setInstruction}
                  />
                </div>

                <div className="bg-white rounded-xl border border-[var(--gray-200)] p-6">
                  <button
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    className="flex items-center justify-between w-full mb-4 hover:text-[var(--primary-600)] transition-colors"
                  >
                    <h3>高级选项</h3>
                    <motion.div
                      animate={{ rotate: showAdvanced ? 180 : 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <ChevronDown size={20} />
                    </motion.div>
                  </button>

                  <AnimatePresence>
                    {showAdvanced && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="space-y-4"
                      >
                        <div>
                          <label className="block text-sm mb-2" style={{ color: 'var(--gray-600)' }}>
                            处理质量
                          </label>
                          <select className="w-full p-3 border border-[var(--gray-200)] rounded-lg focus:outline-none focus:border-[var(--primary-500)]">
                            <option>标准质量 (推荐)</option>
                            <option>高质量 (处理时间更长)</option>
                            <option>超高质量 (最慢)</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm mb-2" style={{ color: 'var(--gray-600)' }}>
                            输出分辨率
                          </label>
                          <select className="w-full p-3 border border-[var(--gray-200)] rounded-lg focus:outline-none focus:border-[var(--primary-500)]">
                            <option>1920x1080 (Full HD)</option>
                            <option>1280x720 (HD)</option>
                            <option>3840x2160 (4K)</option>
                          </select>
                        </div>

                        <div className="flex items-center gap-3">
                          <input type="checkbox" id="keepAudio" className="w-4 h-4" />
                          <label htmlFor="keepAudio" className="text-sm" style={{ color: 'var(--gray-600)' }}>
                            保留原始音频
                          </label>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                <motion.button
                  onClick={handleStartProcessing}
                  disabled={!uploadedVideo || !instruction.trim()}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full py-4 rounded-xl font-medium flex items-center justify-center gap-2
                    disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                  style={{
                    backgroundColor: uploadedVideo && instruction.trim() ? 'var(--primary-600)' : 'var(--gray-300)',
                    color: 'white',
                  }}
                >
                  <Zap size={20} />
                  <span>开始处理</span>
                </motion.button>
              </div>
            </motion.div>
          )}

          {appState === 'processing' && (
            <motion.div
              key="processing"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              <div className="bg-white rounded-xl border border-[var(--gray-200)] p-6">
                <ProgressIndicator
                  currentStep={currentStep}
                  totalSteps={steps.length}
                  steps={steps}
                  progress={progress}
                  estimatedTime={estimatedTime}
                  currentIteration={currentIteration}
                  totalIterations={3}
                />
              </div>

              <div className="grid lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-xl border border-[var(--gray-200)] p-6">
                  <VideoPreview 
                    title="原始视频"
                    videoUrl={uploadedVideo ? URL.createObjectURL(uploadedVideo) : undefined}
                    isOriginal
                  />
                </div>

                <div className="bg-white rounded-xl border border-[var(--gray-200)] p-6">
                  <VideoPreview 
                    title="处理预览"
                  />
                </div>
              </div>
            </motion.div>
          )}

          {appState === 'result' && (
            <motion.div
              key="result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              <div className="bg-gradient-to-r from-[var(--success)]/10 to-[var(--success)]/5 rounded-xl border border-[var(--success)]/20 p-6">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-full bg-[var(--success)] flex items-center justify-center">
                    <Zap className="text-white" size={20} />
                  </div>
                  <h2 style={{ color: 'var(--success)' }}>处理完成！</h2>
                </div>
                <p className="text-sm" style={{ color: 'var(--gray-600)' }}>
                  您的视频已成功处理完成，可以预览和下载结果
                </p>
              </div>

              <div className="grid lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-xl border border-[var(--gray-200)] p-6">
                  <VideoPreview 
                    title="原始视频"
                    videoUrl={uploadedVideo ? URL.createObjectURL(uploadedVideo) : undefined}
                    isOriginal
                  />
                </div>

                <div className="bg-white rounded-xl border border-[var(--gray-200)] p-6">
                  <VideoPreview 
                    title="处理结果"
                    videoUrl={uploadedVideo ? URL.createObjectURL(uploadedVideo) : undefined}
                  />
                </div>
              </div>

              <div className="flex gap-4">
                <motion.button
                  onClick={handleDownload}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex-1 py-4 rounded-xl font-medium"
                  style={{
                    backgroundColor: 'var(--primary-600)',
                    color: 'white',
                  }}
                >
                  下载视频
                </motion.button>
                
                <motion.button
                  onClick={handleReset}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-6 py-4 rounded-xl font-medium border-2"
                  style={{
                    borderColor: 'var(--gray-200)',
                    color: 'var(--gray-600)',
                  }}
                >
                  开始新项目
                </motion.button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
