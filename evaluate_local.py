import os
import glob
import pandas as pd
import jiwer
import sys
import argparse
from transcriber import transcribe_audio

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

def normalize_text(text):
    """Simple normalization to make comparison fairer."""
    if not isinstance(text, str):
        return ""
    # Remove punctuation and lower case (though Arabic doesn't have casing, it helps for other langs)
    # Customize for Arabic if needed (e.g. removing diacritics), but starting simple.
    text = text.lower().strip()
    chars_to_remove = ['.', ',', '?', '!', ':', ';', '-', '_', '"', "'", '(', ')', '[', ']', '{', '}']
    for c in chars_to_remove:
        text = text.replace(c, '')
    return text

def evaluate_folder(target_dir, model_size='base'):
    print(f"Scanning {target_dir}...")
    
    audio_files = glob.glob(os.path.join(target_dir, "**", "*.mp3"), recursive=True)
    
    results = []
    total_wer = 0
    count = 0
    
    print(f"Found {len(audio_files)} audio files.")
    
    for audio_path in audio_files:
        audio_dir = os.path.dirname(audio_path)
        gt_path = os.path.join(audio_dir, "letra.txt")
        
        if not os.path.exists(gt_path):
            print(f"[WARN] No letra.txt found for {os.path.basename(audio_path)}, skipping.")
            continue
            
        print(f"\nProcessing: {os.path.basename(audio_path)}")
        
        try:
            # 1. Get Ground Truth
            with open(gt_path, 'r', encoding='utf-8') as f:
                reference_text = f.read()
                
            # 2. Transcribe
            hypothesis_text = transcribe_audio(audio_path, model_size=model_size)
            
            # 3. Calculate WER
            ref_norm = normalize_text(reference_text)
            hyp_norm = normalize_text(hypothesis_text)
            
            if not ref_norm:
                print(f"[WARN] Reference text empty for {os.path.basename(audio_path)}, skipping metric.")
                continue

            error = jiwer.wer(ref_norm, hyp_norm)
            
            print(f"  WER: {error:.4f}")
            # print(f"  Ref: {ref_norm[:50]}...")
            # print(f"  Hyp: {hyp_norm[:50]}...")
            
            results.append({
                'file': os.path.basename(audio_path),
                'reference': reference_text,
                'hypothesis': hypothesis_text,
                'ref_norm': ref_norm,
                'hyp_norm': hyp_norm,
                'wer': error
            })
            
            total_wer += error
            count += 1
            
        except Exception as e:
            print(f"[ERROR] Failed to process {os.path.basename(audio_path)}: {e}")
            
    if count > 0:
        avg_wer = total_wer / count
        print("\n" + "="*40)
        print(f"Evaluation Complete")
        print(f"Files Processed: {count}")
        print(f"Average WER: {avg_wer:.4f} ({avg_wer*100:.2f}%)")
        print("="*40)
        
        output_csv = "evaluation_local_results.csv"
        pd.DataFrame(results).to_csv(output_csv, index=False, encoding='utf-8-sig') # utf-8-sig for Excel
        print(f"Detailed results saved to {output_csv}")
    else:
        print("No valid samples processed (checked audio files and confirmed occurrence of letra.txt).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate transcription on local folder.")
    parser.add_argument("--dir", default=r"c:\Users\jorge\OneDrive\Documentos\Prácticas\Scripts\Lyric transcriptor\test_data\465 - أرحنا بالصلاة يا بلال", help="Target directory")
    parser.add_argument("--model", default="base", help="Whisper model size")
    
    args = parser.parse_args()
    
    evaluate_folder(args.dir, args.model)
