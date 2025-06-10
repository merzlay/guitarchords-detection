import zipfile, os, glob
import pandas as pd
import os
from google.colab import files

uploaded = '/content/annotationcsv.zip'
extract_dir = "/content/annotationextracted"
with zipfile.ZipFile(uploaded, 'r') as zip_ref:
    zip_ref.extractall(extract_dir)

import music21
from music21 import pitch
from tqdm import tqdm

zip_path = '/content/annotationcsv.zip'
extract_dir = "/content/annotationextracted"
os.makedirs(extract_dir, exist_ok=True)

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_dir)

base_midi = {
    6: 40, 5: 45, 4: 50, 3: 55, 2: 59, 1: 64
}

bin_size = 2.0
csv_files = glob.glob(os.path.join(extract_dir, "**", "*.csv"), recursive=True)

output_dir = "/content/chordoutput"
os.makedirs(output_dir, exist_ok=True)

def predict_chords_from_csv(csv_path):
    try:
        df = pd.read_csv(csv_path)
        df = df.dropna(subset=['start_time', 'end_time', 'string', 'fret'])
        df['start_time'] = df['start_time'].astype(float)
        df['end_time'] = df['end_time'].astype(float)
        df['string'] = df['string'].astype(int)
        df['fret'] = df['fret'].astype(int)
        df['time_bin'] = df['start_time'].apply(lambda t: int(t // bin_size))

        chord_segments = []

        for time_bin, group in df.groupby('time_bin'):
            midi_pitches = []
            for _, row in group.iterrows():
                string = row['string']
                fret = row['fret']
                if string in base_midi:
                    midi = base_midi[string] + fret
                    midi_pitches.append(midi)

            try:
                note_names = [pitch.Pitch(m).getEnharmonic().name for m in midi_pitches]
                note_names = sorted(set(note_names))
            except:
                note_names = []

            if len(note_names) < 3 or len(note_names) > 6:
                chord_name = "Unknown"
            else:
                try:
                    chord_obj = music21.chord.Chord(note_names)
                    chord_symbol = music21.harmony.chordSymbolFromChord(chord_obj)
                    chord_name = chord_symbol.figure
                    if "Cannot Be Identified" in chord_name:
                        raise Exception("Fallback")
                except:
                    try:
                        root = chord_obj.root().name
                        quality = chord_obj.quality
                        if quality == 'major':
                            chord_name = root
                        elif quality == 'minor':
                            chord_name = root + 'm'
                        elif quality == 'diminished':
                            chord_name = root + 'dim'
                        elif quality == 'augmented':
                            chord_name = root + 'aug'
                        elif quality == 'dominant':
                            chord_name = root + '7'
                        else:
                            chord_name = root + '?'
                    except:
                        chord_name = "Unknown"

            chord_segments.append({
                "start_time": time_bin * bin_size,
                "end_time": (time_bin + 1) * bin_size,
                "chord": chord_name
            })

        return pd.DataFrame(chord_segments)
    except Exception as e:
        print(f"Error in {csv_path}: {e}")
        return None

for file in csv_files:
    print(f"Predicting chords in: {os.path.basename(file)}")
    chord_df = predict_chords_from_csv(file)
    if chord_df is not None:
        output_path = os.path.join(output_dir, os.path.basename(file).replace(".csv", "_chords.csv"))
        chord_df.to_csv(output_path, index=False)
        print(f"Saved to: {output_path}\n")
    else:
        print(f"Failed to process {file}\n")
