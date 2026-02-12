import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

# Load results
df = pd.read_csv('evaluation_hf_results.csv')

# Create figure with subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: WER per sample (bar chart)
ax1.bar(df['id'], df['wer'], color='steelblue', alpha=0.7, edgecolor='black')
ax1.axhline(y=df['wer'].mean(), color='red', linestyle='--', linewidth=2, label=f'Average WER: {df["wer"].mean():.4f}')
ax1.set_xlabel('Sample ID', fontsize=12, fontweight='bold')
ax1.set_ylabel('Word Error Rate (WER)', fontsize=12, fontweight='bold')
ax1.set_title('WER per Sample', fontsize=14, fontweight='bold')
ax1.legend()
ax1.grid(axis='y', alpha=0.3)

# Plot 2: WER distribution (histogram)
ax2.hist(df['wer'], bins=10, color='coral', alpha=0.7, edgecolor='black')
ax2.axvline(x=df['wer'].mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {df["wer"].mean():.4f}')
ax2.axvline(x=df['wer'].median(), color='green', linestyle='--', linewidth=2, label=f'Median: {df["wer"].median():.4f}')
ax2.set_xlabel('Word Error Rate (WER)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Frequency', fontsize=12, fontweight='bold')
ax2.set_title('WER Distribution', fontsize=14, fontweight='bold')
ax2.legend()
ax2.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('wer_analysis.png', dpi=300, bbox_inches='tight')
print("✓ Gráfica guardada como 'wer_analysis.png'")
print(f"\nEstadísticas:")
print(f"  - WER Promedio: {df['wer'].mean():.4f} ({df['wer'].mean()*100:.2f}%)")
print(f"  - WER Mediana:  {df['wer'].median():.4f} ({df['wer'].median()*100:.2f}%)")
print(f"  - WER Mínimo:   {df['wer'].min():.4f} ({df['wer'].min()*100:.2f}%)")
print(f"  - WER Máximo:   {df['wer'].max():.4f} ({df['wer'].max()*100:.2f}%)")
print(f"  - Desv. Est.:   {df['wer'].std():.4f}")

plt.show()
