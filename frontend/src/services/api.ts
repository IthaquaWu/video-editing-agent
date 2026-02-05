// API服务 - 后端接口集成
export interface UploadResponse {
  videoId: string;
  filename: string;
  size: number;
  duration: number;
}

export interface ProcessRequest {
  videoId: string;
  instruction: string;
  quality?: string;
  resolution?: string;
  keepAudio?: boolean;
}

export interface ProcessStatus {
  videoId: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  currentStep: string;
  estimatedTime: number;
  resultUrl?: string;
  error?: string;
}

class ApiService {
  private baseUrl = 'http://localhost:8000/api'; // 根据实际后端地址调整

  // 上传视频文件
  async uploadVideo(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('video', file);
    
    const response = await fetch(`${this.baseUrl}/upload`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`上传失败: ${response.statusText}`);
    }
    
    return response.json();
  }

  // 开始视频处理
  async startProcessing(request: ProcessRequest): Promise<{ taskId: string }> {
    const response = await fetch(`${this.baseUrl}/process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      throw new Error(`处理请求失败: ${response.statusText}`);
    }
    
    return response.json();
  }

  // 查询处理状态
  async getProcessStatus(videoId: string): Promise<ProcessStatus> {
    const response = await fetch(`${this.baseUrl}/status/${videoId}`);
    
    if (!response.ok) {
      throw new Error(`状态查询失败: ${response.statusText}`);
    }
    
    return response.json();
  }

  // 下载处理结果
  async downloadResult(videoId: string): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/download/${videoId}`);
    
    if (!response.ok) {
      throw new Error(`下载失败: ${response.statusText}`);
    }
    
    return response.blob();
  }
}

export const apiService = new ApiService();