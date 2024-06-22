class Tone:
    PITCHES = "c,c#,d,d#,e,f,f#,g,g#,a,a#,b".split(",")

    def note(name):
        octave = int(name[-1])
        pitch = Tone.PITCHES.index(name[:-1].lower())
        return 440 * 2 ** ((octave - 4) + (pitch - 9) / 12.)

    def play_tone(self, freq: int, duration: float):
        pass

    def play_note(self, note: str, duration: float):
        self.play_tone(Tone.note(note), duration)

    def play_notes(self, tones: list[(int, float)]):
        for (notename, duration) in tones:
            self.play_tone(Tone.note(notename), duration)


    def tone(self, freq: int, duration: float):
        pass

    def success(self):
        self.play_notes([("F4", 0.1)])

    def shake(self):
        self.play_notes([
            ("A4", 0.1),
            ("E4", 0.1),
            ("A4", 0.1),
            ("E4", 0.1),
        ])

    def error(self):
        self.play_notes([
            ("C4", 0.1),
            ("B4", 0.2),
        ])

    def cascade(self):
        self.play_notes([
            ("C4", 0.1),
            ("D4", 0.1),
            ("E4", 0.1),
            ("F4", 0.1),
            ("G4", 0.1),
            ("A4", 0.1),
            ("B4", 0.1),
        ])