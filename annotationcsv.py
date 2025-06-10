!pip install jams
!pip install numpy==1.23.5
!pip install --upgrade jams

import os
import jams
import pandas as pd

def midi_to_fret(midi_note):
    tuning = [64, 59, 55, 50, 45, 40]
    for string in range(6):
        fret = midi_note - tuning[string]
        if 0 <= fret <= 24:
            return (string + 1, fret)
    return (None, None)

output_dir = 'annotationcsv'
os.makedirs(output_dir, exist_ok=True)

input_folder = '/content/annotation(jams)'

for filename in os.listdir(input_folder):
    if filename.endswith('.jams'):
        jam_path = os.path.join(input_folder, filename)
        jam = jams.load(jam_path)
        notes = jam.search(namespace='note_midi')

        data = []
        for annotation in notes:
            for note in annotation.data:
                if isinstance(note.value, dict):
                    string = note.value.get('string')
                    fret = note.value.get('fret')
                    midi_pitch = None
                else:
                    midi_pitch = note.value
                    string, fret = midi_to_fret(midi_pitch)
                if string is not None and fret is not None:
                    entry = {
                        'start_time': note.time,
                        'end_time': note.time + note.duration,
                        'string': string,
                        'fret': fret,
                        'duration': note.duration,
                        'midi_pitch': midi_pitch
                    }
                    data.append(entry)
        if data:
            df = pd.DataFrame(data)
            csv_filename = os.path.splitext(filename)[0] + '.csv'
            csv_path = os.path.join(output_dir, csv_filename)
            df.to_csv(csv_path, index=False)
            print(f"Saved: {csv_path}")
        else:
            print(f"No note data in: {filename}")

import shutil
from google.colab import files

shutil.make_archive("annotationcsv", 'zip', "annotationcsv")
