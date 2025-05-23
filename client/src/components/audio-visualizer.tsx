import { useEffect, useRef } from "react";

interface AudioVisualizerProps {
  isActive: boolean;
}

export function AudioVisualizer({ isActive }: AudioVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const audioContextRef = useRef<AudioContext>();
  const analyserRef = useRef<AnalyserNode>();
  const dataArrayRef = useRef<Uint8Array>();

  useEffect(() => {
    if (isActive) {
      startVisualization();
    } else {
      stopVisualization();
    }

    return () => {
      stopVisualization();
    };
  }, [isActive]);

  const startVisualization = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      
      source.connect(analyserRef.current);
      analyserRef.current.fftSize = 256;
      
      const bufferLength = analyserRef.current.frequencyBinCount;
      dataArrayRef.current = new Uint8Array(bufferLength);
      
      animate();
    } catch (error) {
      console.error('Error accessing microphone for visualization:', error);
      // Fallback to static animation
      animateStatic();
    }
  };

  const stopVisualization = () => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }
  };

  const animate = () => {
    if (!isActive) return;

    const canvas = canvasRef.current;
    const analyser = analyserRef.current;
    const dataArray = dataArrayRef.current;

    if (!canvas || !analyser || !dataArray) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    analyser.getByteFrequencyData(dataArray);

    ctx.fillStyle = 'rgb(15, 23, 42)'; // slate-900
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const barWidth = (canvas.width / dataArray.length) * 2.5;
    let barHeight;
    let x = 0;

    for (let i = 0; i < dataArray.length; i++) {
      barHeight = (dataArray[i] / 255) * canvas.height * 0.8;

      // Create gradient for bars
      const gradient = ctx.createLinearGradient(0, canvas.height - barHeight, 0, canvas.height);
      gradient.addColorStop(0, '#059669'); // emerald-600
      gradient.addColorStop(0.5, '#10B981'); // emerald-500
      gradient.addColorStop(1, '#3B82F6'); // blue-500

      ctx.fillStyle = gradient;
      ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

      x += barWidth + 1;
    }

    animationRef.current = requestAnimationFrame(animate);
  };

  const animateStatic = () => {
    if (!isActive) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.fillStyle = 'rgb(15, 23, 42)'; // slate-900
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Static wave animation
    const bars = 32;
    const barWidth = canvas.width / bars;
    
    for (let i = 0; i < bars; i++) {
      const height = Math.sin((Date.now() * 0.01) + (i * 0.3)) * 20 + 30;
      
      const gradient = ctx.createLinearGradient(0, canvas.height - height, 0, canvas.height);
      gradient.addColorStop(0, '#059669'); // emerald-600
      gradient.addColorStop(0.5, '#10B981'); // emerald-500
      gradient.addColorStop(1, '#3B82F6'); // blue-500

      ctx.fillStyle = gradient;
      ctx.fillRect(i * barWidth, canvas.height - height, barWidth - 1, height);
    }

    animationRef.current = requestAnimationFrame(animateStatic);
  };

  return (
    <div className="w-full h-16 flex items-center justify-center">
      {isActive ? (
        <canvas
          ref={canvasRef}
          width={200}
          height={64}
          className="rounded-lg"
        />
      ) : (
        <div className="flex items-end space-x-1 opacity-30">
          {[...Array(7)].map((_, i) => (
            <div
              key={i}
              className="w-1 bg-emerald-600 rounded-full animate-pulse"
              style={{
                height: `${8 + (i % 3) * 4}px`,
                animationDelay: `${i * 0.1}s`
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
