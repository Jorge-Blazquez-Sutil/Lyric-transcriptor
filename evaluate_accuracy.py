import os
import pandas as pd
import jiwer
import argparse
import whisper
import warnings
import io
import torchaudio
import torch
import numpy as np
import soundfile as sf
from datasets import load_dataset, Audio

# Suppress warnings
warnings.filterwarnings("ignore")

def normalize_text(text):
    """Simple normalization to make comparison fairer."""
    if not isinstance(text, str):
        return ""
    # Remove punctuation and lower case
    return text.lower().strip().replace('.', '').replace(',', '').replace('?', '').replace('!', '')

def decode_audio_bytes(audio_bytes, target_sr=16000):
    """
    Manually decode audio bytes using soundfile (primary) or torchaudio (fallback).
    This bypasses datasets' internal decoding which can be fragile on Windows.
    Returns: numpy float32 array at target_sr.
    """
    try:
        # Try soundfile first (very robust for standard formats)
        audio_file = io.BytesIO(audio_bytes)
        data, samplerate = sf.read(audio_file)
        
        # Convert to float32
        data = data.astype("float32")
        
        # Resample if needed
        if samplerate != target_sr:
             # Convert to torch for reliable resampling
             waveform = torch.from_numpy(data)
             if waveform.dim() == 1:
                 waveform = waveform.unsqueeze(0) # (1, time)
             if waveform.dim() == 2 and waveform.shape[1] < waveform.shape[0]:
                 # soundfile returns (time, channels), torch expects (channels, time)
                 waveform = waveform.t()
                 
             resampler = torchaudio.transforms.Resample(orig_freq=samplerate, new_freq=target_sr)
             waveform = resampler(waveform)
             
             # Convert back to simple numpy array (mono)
             return waveform.mean(dim=0).numpy()
            
        return data
        
    except Exception as e:
        # Fallback to torchaudio load if soundfile fails (e.g. strict formats)
        try:
             audio_file = io.BytesIO(audio_bytes)
             waveform, sample_rate = torchaudio.load(audio_file)
             if sample_rate != target_sr:
                 resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=target_sr)
                 waveform = resampler(waveform)
             return waveform.mean(dim=0).numpy()
        except Exception as e2:
            print(f"Error decoding audio: {e2}")
            return None

def evaluate_hf(dataset_name, config_name, split, num_samples, model_size='base', streaming=False):
    print(f"Loading dataset {dataset_name} ({config_name}) split '{split}' (streaming={streaming})...")
    try:
        ds = load_dataset(dataset_name, config_name, split=split, streaming=streaming)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    # Disable automatic decoding to avoid 'torchcodec' DLL errors on Windows make sure to only do this if not streaming, as streaming might handle it differently or fail on cast
    # Disable automatic decoding to avoid 'torchcodec' DLL errors on Windows
    # This must be done even for streaming datasets if possible.
    try:
        ds = ds.cast_column("audio", Audio(decode=False))
        print("DEBUG: Decoding disabled successfully.")
    except Exception as e:
        print(f"Warning: Could not disable automatic decoding: {e}")

    # Select subset
    if not streaming and num_samples and num_samples < len(ds):
        ds = ds.select(range(num_samples))
        print(f"Selected {num_samples} samples for evaluation.")
    elif not streaming:
        print(f"Evaluating on all {len(ds)} samples.")

    print(f"Loading Whisper model '{model_size}'...")
    model = whisper.load_model(model_size)

    results = []
    total_wer = 0
    count = 0

    print("Starting evaluation loop...")
    
    # If streaming, we just take the first N samples
    iterator = iter(ds) if streaming else ds
    
    for i, sample in enumerate(iterator):
        if streaming and num_samples and i >= num_samples:
            break
            
        try:
            # Handle audio data manually
            audio_data = sample['audio']
            
            # Streaming datasets often return audio as {'array': ..., 'sampling_rate': ...} if decoded,
            # OR {'bytes': ...} if we managed to disable decoding.
            # But cast_column might not work well with streaming.
            # If streaming, 'datasets' defaults to decoding.
            # If we get 'array', we use it directly (but check SR).
            
            audio_array = None
            
            if 'array' in audio_data:
                # Valid decoded audio
                audio_array = audio_data['array'].astype("float32")
                sr = audio_data['sampling_rate']
                if sr != 16000:
                    # Resample
                    waveform = torch.from_numpy(audio_array)
                    resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
                    audio_array = resampler(waveform).numpy()
            elif 'bytes' in audio_data:
                # Bytes available
                audio_bytes = audio_data['bytes']
                if audio_bytes:
                     audio_array = decode_audio_bytes(audio_bytes)
            elif 'path' in audio_data and audio_data['path'] and os.path.exists(audio_data['path']):
                # Local path
                with open(audio_data['path'], 'rb') as f:
                    audio_array = decode_audio_bytes(f.read())

            if audio_array is None:
                print(f"Skipping sample {i}: Could not extract audio.")
                continue

            reference_text = sample['text']
            
            # Transcribe
            transcription = model.transcribe(audio_array)
            hypothesis_text = transcription['text']

            # Metrics
            ref_norm = normalize_text(reference_text)
            hyp_norm = normalize_text(hypothesis_text)
            error = jiwer.wer(ref_norm, hyp_norm)
            
            results.append({
                'id': i,
                'reference': reference_text,
                'hypothesis': hypothesis_text,
                'wer': error
            })
            
            total_wer += error
            count += 1
            
            print(f"Processed {i + 1}/{num_samples if num_samples else 'All'}: Last WER = {error:.2f}")

        except Exception as e:
            print(f"Error processing sample {i}: {e}")

    if count > 0:
        avg_wer = total_wer / count
        print("\n" + "="*40)
        print(f"Evaluation Complete")
        print(f"Processed: {count}")
        print(f"Average WER: {avg_wer:.4f} ({avg_wer*100:.2f}%)")
        print("="*40)
        
        output_csv = "evaluation_hf_results.csv"
        pd.DataFrame(results).to_csv(output_csv, index=False)
        print(f"Detailed results saved to {output_csv}")
    else:
        print("No samples were processed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate transcription accuracy using Hugging Face datasets.")
    parser.add_argument("--dataset", default="google/WaxalNLP", help="HF Dataset name")
    parser.add_argument("--config", default="ach_tts", help="Dataset configuration")
    parser.add_argument("--split", default="train", help="Dataset split (train/test/validation)")
    parser.add_argument("--num_samples", type=int, default=10, help="Number of samples to evaluate (default: 10)")
    parser.add_argument("--model", default="base", help="Whisper model size")
    parser.add_argument("--streaming", action="store_true", help="Enable streaming mode")
    
    args = parser.parse_args()
    
    evaluate_hf(args.dataset, args.config, args.split, args.num_samples, args.model, args.streaming)
