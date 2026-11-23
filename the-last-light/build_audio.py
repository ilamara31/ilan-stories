"""The Last Light — builds the full soundtrack (voices + music + sound effects) and timeline.json.
Voices: macOS built-in `say` voices (free, offline). Music + effects: synthesized here with numpy.
Run:  ../.venv/bin/python build_audio.py   →  story.m4a + timeline.json
"""
import json, os, subprocess, wave
import numpy as np

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
VDIR = os.path.join(HERE, 'voice')
VOICES = {
    'N': ('Daniel', 158),                       # narrator
    'E': ('Grandpa (English (UK))', 150),       # Elias, the old keeper
    'M': ('Flo (English (US))', 178),           # Mira
}

# ---------- the script: scenes made of lines / pauses / sound events ----------
S = [
  ('title', [('pause', 2.2), ('ev', 'titleIn'),
     ('N', "On the edge of the world, there is a town called Saltmere."), ('pause', .5),
     ('N', "And on the cliffs above Saltmere stands a lighthouse that has never gone dark."), ('pause', .35),
     ('N', "Not once, in a hundred years."), ('pause', 1.0)]),
  ('keeper', [('pause', .3),
     ('N', "Its keeper was old Elias. And every evening, his granddaughter Mira climbed the two hundred steps to help him."), ('pause', .7)]),
  ('rules', [('pause', .4),
     ('E', "Three rules, Mira. Keep the glass clean. Keep the flame burning."), ('pause', .45),
     ('E', "And never, ever look at the sea when the light goes out."), ('pause', .5),
     ('M', "Why not?"), ('pause', .7),
     ('E', "Because the sea, looks back."), ('pause', .8),
     ('N', "Mira laughed. She thought it was just another one of Grandpa's stories."), ('pause', .8)]),
  ('storm', [('ev', 'thunder'), ('pause', 1.6),
     ('N', "Then came the night of the great storm."), ('pause', 1.0),
     ('ev', 'thunder2'), ('pause', .25), ('ev', 'lightOut'), ('pause', 2.2)]),
  ('bedroom', [('pause', .6),
     ('N', "At midnight, Mira woke up. Her room was dark. Too dark. The lighthouse beam had stopped."), ('pause', .6),
     ('M', "Grandpa?"), ('pause', .9),
     ('N', "His chair was empty. The door to the tower was swinging in the wind."), ('ev', 'door'), ('pause', .5),
     ('M', "Grandpa! Where are you?"), ('pause', .7)]),
  ('stairs', [('ev', 'steps'), ('pause', .5),
     ('N', "Mira grabbed a lantern, and climbed."), ('pause', .4),
     ('N', "Fifty steps."), ('pause', .5), ('N', "One hundred."), ('pause', .5), ('N', "Two hundred."), ('pause', .9), ('ev', 'stepsEnd')]),
  ('logbook', [('pause', .4),
     ('N', "At the top, the great lamp was cold. And on the table lay Grandpa's logbook, open to the last page."), ('pause', .6),
     ('ev', 'write'),
     ('E', "If you are reading this, the light has gone out. Light it again. Quickly. Before they wake up."), ('pause', .8)]),
  ('relight', [('N', "Her hands were shaking. One match."), ('ev', 'match1'), ('pause', .9), ('N', "Two."), ('ev', 'match2'), ('pause', .7),
     ('N', "Then"), ('pause', .35), ('ev', 'whoosh'), ('pause', 2.4),
     ('N', "The light roared back to life. And Mira did the one thing she was never supposed to do."), ('pause', .7),
     ('N', "She looked at the sea."), ('pause', 1.2)]),
  ('city', [('ev', 'cityRise'), ('pause', 1.4),
     ('N', "Deep beneath the waves, lights were glowing. Windows. Towers. Streets."), ('pause', .45),
     ('N', "A whole city, at the bottom of the ocean."), ('pause', .45),
     ('N', "And it was waking up."), ('pause', 1.3)]),
  ('figure', [('N', "Then, on the rocks below, someone walked out of the water."), ('pause', 1.2),
     ('M', "Grandpa?!"), ('pause', .8)]),
  ('twist', [('E', "Mira. I told you not to look."), ('pause', .7),
     ('M', "What is that place? What's going on?"), ('pause', .8),
     ('E', "The light was never keeping monsters away from Saltmere, Mira."), ('pause', .8),
     ('ev', 'boom'), ('E', "It was keeping us, away from you."), ('pause', 1.0),
     ('M', "Us?"), ('pause', 1.0),
     ('E', "Your mother is down there. And she has been waiting, a very long time."), ('pause', 1.3)]),
  ('hand', [('N', "The beam flickered. And when Mira looked down at her own hand,"), ('pause', .5), ('ev', 'glow'),
     ('N', "it was glowing. The same deep blue as the sea."), ('pause', 1.8)]),
  ('end', [('ev', 'sting'), ('pause', 1.2),
     ('N', "The Last Light. Part two. The City Below."), ('pause', .6), ('N', "Coming soon."), ('pause', 4.5)]),
]

def tts(who, text, idx):
    voice, rate = VOICES[who]
    path = os.path.join(VDIR, f'{idx:02d}_{who}.wav')
    key = path + '.txt'
    if not (os.path.exists(path) and os.path.exists(key) and open(key).read() == f'{voice}|{rate}|{text}'):
        subprocess.run(['say', '-v', voice, '-r', str(rate), '--data-format=LEI16@44100', '-o', path, text], check=True)
        open(key, 'w').write(f'{voice}|{rate}|{text}')
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        if w.getnchannels() == 2: a = a.reshape(-1, 2).mean(1)
    # trim silence at both ends
    nz = np.where(np.abs(a) > 0.01)[0]
    if len(nz): a = a[max(0, nz[0] - 400): nz[-1] + 1200]
    return a

# ---------- lay out the timeline ----------
t = 0.0; scenes = []; cues = []; events = []; clips = []; idx = 0
for sid, items in S:
    s0 = t
    for it in items:
        if it[0] == 'pause': t += it[1]
        elif it[0] == 'ev': events.append({'name': it[1], 't': round(t, 3)})
        else:
            who, text = it
            a = tts(who, text, idx); idx += 1
            d = len(a) / SR
            clips.append((t, who, a))
            cues.append({'who': who, 'text': text, 't0': round(t, 3), 't1': round(t + d, 3)})
            t += d + 0.12
    scenes.append({'id': sid, 't0': round(s0, 3), 't1': round(t, 3)})
TOTAL = t + 0.5
N = int(TOTAL * SR)
print(f'total {TOTAL:.1f}s, {len(cues)} lines')
ev = {e['name']: e['t'] for e in events}
sc = {s['id']: (s['t0'], s['t1']) for s in scenes}

# ---------- synth helpers ----------
rng = np.random.default_rng(7)
def tt(n): return np.arange(n) / SR
def shaped_noise(n, lo, hi, tilt=0.0, seed=None):
    r = np.random.default_rng(seed) if seed is not None else rng
    x = r.standard_normal(n)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR)
    m = ((f >= lo) & (f <= hi)).astype(float)
    # soft edges
    m = np.where(f < lo, np.exp(-((lo - f) / (lo * .5 + 1)) ** 2), m)
    m = np.where(f > hi, np.exp(-((f - hi) / (hi * .3 + 1)) ** 2), m)
    if tilt: m *= (np.maximum(f, 20) / 1000.0) ** tilt
    y = np.fft.irfft(X * m, n)
    return y / (np.abs(y).max() + 1e-9)
def env_adsr(n, a, d, s, r):
    e = np.ones(n) * s; A = int(a * SR); D = int(d * SR); R = int(r * SR)
    A = min(A, n); e[:A] = np.linspace(0, 1, A)
    if D: e[A:A + D] = np.linspace(1, s, len(e[A:A + D]))
    if R: e[max(0, n - R):] *= np.linspace(1, 0, len(e[max(0, n - R):]))
    return e
def mf(m): return 440 * 2 ** ((m - 69) / 12)

L = np.zeros(N); Rr = np.zeros(N)     # music + fx bus (stereo)
V = np.zeros(N)                       # voice bus (mono, centred)
def add(sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N: return
    sig = sig[:N - i]
    gl = gain * np.sqrt((1 - pan) / 2) * 1.41; gr = gain * np.sqrt((1 + pan) / 2) * 1.41
    L[i:i + len(sig)] += sig * gl; Rr[i:i + len(sig)] += sig * gr

# pad: soft detuned chord with slow attack
def pad(notes, dur, bright=1.0, vib=0.0):
    n = int(dur * SR); x = tt(n); y = np.zeros(n)
    for m in notes:
        for det in (-0.07, 0.0, 0.06):
            f = mf(m + det)
            ph = 2 * np.pi * f * x + (vib * np.sin(2 * np.pi * 5.2 * x) if vib else 0)
            y += np.sin(ph) + 0.25 * bright * np.sin(2 * ph) + 0.08 * bright * np.sin(3 * ph)
    y /= len(notes) * 3
    return y * env_adsr(n, min(2.5, dur / 3), 0, 1, min(3.0, dur / 3))
def bell(m, dur=3.0):
    n = int(dur * SR); x = tt(n)
    y = (np.sin(2 * np.pi * mf(m) * x) + .4 * np.sin(2 * np.pi * mf(m) * 2.76 * x) * np.exp(-x * 3) + .2 * np.sin(2 * np.pi * mf(m) * 5.4 * x) * np.exp(-x * 6))
    return y * np.exp(-x * 1.4) * np.minimum(1, x * 400)
def piano(m, dur=2.5, vel=1.0):
    n = int(dur * SR); x = tt(n); f = mf(m)
    y = sum(a * np.sin(2 * np.pi * f * h * x) for h, a in ((1, 1), (2, .45), (3, .2), (4, .1)))
    return vel * y * np.exp(-x * 1.6) * np.minimum(1, x * 300)
def thump(f0=55, dur=.35, g=1.0):
    n = int(dur * SR); x = tt(n)
    fr = f0 * (1 + 1.5 * np.exp(-x * 30))
    return g * np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-x * 9)
def brass(m, dur):
    n = int(dur * SR); x = tt(n); f = mf(m); y = np.zeros(n)
    for h in range(1, 9): y += np.sin(2 * np.pi * f * h * x + h) / h ** 1.1
    return y / 3 * env_adsr(n, .04, .3, .7, .8)

# ---------- ambience ----------
def sec(a, b): return int(a * SR), int(b * SR)
# ocean waves under title/keeper, city/figure/twist/hand
def ocean(a, b, g):
    i, j = sec(a, b); n = j - i
    base = shaped_noise(n, 60, 900, -0.6)
    lfo = 0.55 + 0.45 * np.sin(2 * np.pi * 0.11 * tt(n) + rng.random() * 6) ** 2
    fade = env_adsr(n, 2.0, 0, 1, 2.0)
    L[i:j] += base * lfo * fade * g
    base2 = shaped_noise(n, 60, 900, -0.6)
    Rr[i:j] += base2 * lfo[::-1] * fade * g
ocean(0, sc['rules'][0] + 1.5, .16)
ocean(sc['city'][0] - .5, sc['hand'][1], .2)
# wind + rain during storm → logbook
def rain(a, b, g):
    i, j = sec(a, b); n = j - i
    fade = env_adsr(n, 1.5, 0, 1, 2.5)
    for ch in (L, Rr):
        r = shaped_noise(n, 2500, 9000, 0.2) * .6 + shaped_noise(n, 300, 1500, -.3) * .35
        drops = np.zeros(n); k = rng.integers(0, n, int((b - a) * 40)); drops[k] = rng.standard_normal(len(k))
        drops = np.convolve(drops, np.exp(-np.arange(200) / 30), mode='same')
        ch[i:j] += (r + drops * .25) * fade * g
rain(sc['storm'][0], sc['stairs'][0] + 1.0, .13)
rain(sc['stairs'][0], sc['relight'][1], .05)
def wind(a, b, g):
    i, j = sec(a, b); n = j - i
    w = shaped_noise(n, 200, 700, -0.5); lfo = .5 + .5 * np.sin(2 * np.pi * .07 * tt(n)) * np.sin(2 * np.pi * .19 * tt(n))
    w *= lfo * env_adsr(n, 2, 0, 1, 2); L[i:j] += w * g; Rr[i:j] += w[::-1] * g
wind(sc['storm'][0], sc['bedroom'][1], .1)
# thunder
def thunder(t0, g=1.0, seed=None):
    n = int(5 * SR); x = tt(n)
    y = shaped_noise(n, 25, 400, -1.0, seed) * np.exp(-x * .9) * np.minimum(1, x * 30)
    crack = shaped_noise(n, 800, 5000, 0, seed) * np.exp(-x * 7)
    add(y * 1.0 + crack * .35, t0, g * .9, -.2); add(shaped_noise(n, 25, 300, -1, (seed or 0) + 3) * np.exp(-x * .7) * np.minimum(1, np.maximum(0, x - .25) * 8), t0, g * .5, .3)
thunder(ev['thunder'], 1.0, 11); thunder(ev['thunder2'], 1.2, 12)
thunder(sc['bedroom'][0] + 6.5, .45, 13)
# light dying: a descending electric whine + thump
n = int(1.6 * SR); x = tt(n)
add(np.sin(2 * np.pi * np.cumsum(420 * np.exp(-x * 2.2) + 40) / SR) * np.exp(-x * 2) * .25, ev['lightOut'], .7)
add(thump(45, .8, 1.0), ev['lightOut'] + .05, .8)
# door creak + bang
n = int(1.4 * SR); x = tt(n)
creak = np.sin(2 * np.pi * np.cumsum(300 + 120 * np.sin(2 * np.pi * 3 * x) + 60 * rng.standard_normal(n).cumsum() / n * 20) / SR) * shaped_noise(n, 200, 2000, 0, 5) * env_adsr(n, .2, 0, 1, .4)
add(creak, ev['door'], .25, .5); add(thump(70, .4) + shaped_noise(int(.4 * SR), 100, 2000, 0, 6) * np.exp(-tt(int(.4 * SR)) * 14) * .5, ev['door'] + 1.3, .55, .5)
# footsteps on the stairs (metal/stone taps) + heartbeat
a0, a1 = ev['steps'], ev['stepsEnd']; k = 0; tstep = a0
while tstep < a1:
    tap = shaped_noise(int(.12 * SR), 300, 3000, 0, 100 + k) * np.exp(-tt(int(.12 * SR)) * 45)
    add(tap + thump(90, .12, .5), tstep, .22 + .08 * (k % 2), -.3 if k % 2 else .3); k += 1
    tstep += .34 - min(.1, (tstep - a0) * .008)
hb = a0;
while hb < a1 + 3:
    add(thump(48, .3, .9), hb, .5); add(thump(44, .3, .7), hb + .22, .4); hb += .95
# logbook scratch-writing
n = int(4.5 * SR); x = tt(n)
scr = shaped_noise(n, 2000, 7000, 0, 21) * (np.abs(np.sin(2 * np.pi * 3.3 * x)) ** 4) * env_adsr(n, .2, 0, 1, .5)
add(scr, ev['write'], .07, .2)
# matches
for nm, g in (('match1', .5), ('match2', .6)):
    n = int(.5 * SR); x = tt(n)
    add(shaped_noise(n, 1500, 9000, 0, 31) * np.exp(-x * 12) * np.minimum(1, x * 200), ev[nm], g)
n = int(1.6 * SR); x = tt(n)
add(shaped_noise(n, 150, 1500, -.4, 32) * env_adsr(n, .05, .3, .4, .9), ev['match2'] + .1, .35)
# WHOOSH: the light returns — rising noise, sub boom, bright chord
n = int(3.0 * SR); x = tt(n)
rise = shaped_noise(n, 200, 6000, 0, 41) * (x / 3) ** 2.5
add(rise, ev['whoosh'] - 3.0 + .05, .55)
add(thump(38, 2.0, 1.2), ev['whoosh'], .9)
add(shaped_noise(int(2.5 * SR), 300, 8000, -.2, 42) * np.exp(-tt(int(2.5 * SR)) * 2.2), ev['whoosh'], .35)
for m in (62, 69, 74, 78, 81): add(bell(m, 4), ev['whoosh'] + .02, .12, (m - 72) / 20)
# city rising: choir pad + shimmering bells
cr = ev['cityRise']; dcity = sc['city'][1] - cr + 2
add(pad([50, 57, 62, 65, 69], dcity, .6, vib=.004), cr, .32)
for i2, m in enumerate([74, 77, 81, 86, 81, 77, 79, 84, 86, 89]):
    add(bell(m, 3.5), cr + 1.2 + i2 * 1.05, .06, (-1) ** i2 * .5)
# boom on the twist line
add(thump(32, 2.5, 1.4), ev['boom'] - .05, 1.0)
n = int(2.0 * SR); x = tt(n)
add(shaped_noise(n, 300, 9000, 0, 51) * (x / 2) ** 3, ev['boom'] - 2.0, .28)          # reverse-cymbal swell into it
# glow: magical shimmer
for i2, m in enumerate([81, 85, 88, 93, 88, 93, 97]): add(bell(m, 3), ev['glow'] + i2 * .14, .07, (i2 % 3 - 1) * .6)
add(pad([57, 64, 69, 73], 6, .3, vib=.006), ev['glow'], .2)
# end sting: "dun dun dun DUN"
st = ev['sting']
for i2, (m, d) in enumerate(((38, .35), (38, .35), (38, .35), (41, 2.8))):
    tt0 = st + i2 * .42; add(brass(m, d), tt0, .32); add(brass(m + 12, d), tt0, .16); add(thump(45, .6, 1.0), tt0, .6)
add(pad([50, 53, 57, 62], 7, .5), st + 1.26, .3)

# ---------- score: a quiet piano + pad bed that follows the mood ----------
def bed(a, b, chords, g=.18, arp=True, seed=0):
    span = b - a; per = span / len(chords)
    for k, ch in enumerate(chords):
        add(pad(ch, per + 2.5, .5), a + k * per, g)
        if arp:
            r2 = np.random.default_rng(seed + k)
            for j in range(int(per / .75)):
                m = ch[j % len(ch)] + 12 * (1 + (j // len(ch)) % 2)
                add(piano(m, 2.4, .5), a + k * per + j * .75 + .2, g * .45, r2.uniform(-.6, .6))
Dm, Bb, F, C, Am, Gm, Eb = [50, 57, 62, 65], [46, 53, 58, 62], [41, 53, 57, 60], [48, 55, 60, 64], [45, 52, 57, 60], [43, 50, 55, 58], [39, 46, 51, 55]
bed(sc['title'][0] + 1.5, sc['rules'][1], [Dm, Bb, F, C, Dm, Bb, Gm, Am], .17, True, 1)
bed(sc['bedroom'][0], sc['stairs'][1], [Dm, Eb, Dm, Eb], .12, False, 2)                     # tense, no melody
bed(sc['logbook'][0], sc['relight'][0] + 4, [Gm, Eb], .12, False, 3)
bed(ev['whoosh'] + .5, sc['relight'][1], [F, C], .14, True, 4)
bed(sc['figure'][0], sc['hand'][0], [Dm, Bb, Gm, Am, Dm, Bb], .14, False, 5)
bed(sc['hand'][0], sc['hand'][1], [[45, 52, 57, 61], [45, 52, 57, 64]], .14, True, 6)

# ---------- voices ----------
for t0, who, a in clips:
    i = int(t0 * SR); V[i:i + len(a)] += a * (0.95 if who == 'N' else 1.0)
# duck the music under speech
env = np.convolve(np.abs(V), np.ones(4410) / 4410, mode='same')
env = np.minimum(1, env * 12)
env = np.convolve(env, np.ones(8820) / 8820, mode='same')
duck = 1 - .45 * env
mixL = L * duck + V; mixR = Rr * duck + V
# simple room reverb on the voice for atmosphere (few early reflections)
for d, g in ((.031, .18), (.047, .12), (.071, .09), (.113, .06)):
    k = int(d * SR); mixL[k:] += V[:-k] * g; mixR[k + 37:] += V[:-(k + 37)] * g * .9
peak = max(np.abs(mixL).max(), np.abs(mixR).max())
mixL /= peak / .92; mixR /= peak / .92
# soft clip a touch
mixL = np.tanh(mixL * 1.1) / np.tanh(1.1); mixR = np.tanh(mixR * 1.1) / np.tanh(1.1)
st = (np.stack([mixL, mixR], 1) * 32767).astype(np.int16)
wav = os.path.join(HERE, 'story.wav')
with wave.open(wav, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
subprocess.run(['afconvert', '-f', 'm4af', '-d', 'aac', '-b', '128000', wav, os.path.join(HERE, 'story.m4a')], check=True)
os.remove(wav)
json.dump({'total': round(TOTAL, 2), 'scenes': scenes, 'cues': cues, 'events': events}, open(os.path.join(HERE, 'timeline.json'), 'w'), indent=1)
print('wrote story.m4a', os.path.getsize(os.path.join(HERE, 'story.m4a')) // 1024, 'KB')
