# 2000 to today: passages chosen for this site (no Neuner-Dupuis), whole articles or matched paragraphs.
import re, json
from vat_paras import paras, HEADS
from gen2 import clean, head, fmt
J2, B16, F, L14 = 'John Paul II', 'Benedict XVI', 'Francis', 'Leo XIV'
# key: (id, era, weight, kind, title, date, selection)  selection: article numbers, or regexes matching whole paragraphs
D = {
 'di':   ('DI', J2, 'cdf', 'Declaration of the Congregation for the Doctrine of the Faith', 'Dominus Iesus', '2000-08-06', [4, 5, 6, 7, 9, 10, 11, 14, 15, 16, 17, 20, 21, 22, 23]),
 'nmi':  ('NMI', J2, 'papal', 'Apostolic Letter', 'Novo Millennio Ineunte', '2001-01-06', [29, 43]),
 'pol':  ('DNP', J2, 'cdf', 'Doctrinal Note of the Congregation for the Doctrine of the Faith on some questions regarding the participation of Catholics in political life', None, '2002-11-24', [3, 4]),
 'ede':  ('EDE', J2, 'papal', 'Encyclical Letter', 'Ecclesia de Eucharistia', '2003-04-17', [12, 15, 29, 35, 37, 44, 45, 46]),
 'ssu':  ('CPU', J2, 'cdf', 'Considerations of the Congregation for the Doctrine of the Faith regarding proposals to give legal recognition to unions between homosexual persons', None, '2003-06-03', [4, 5, 10]),
 'dce':  ('DCE', B16, 'papal', 'Encyclical Letter', 'Deus Caritas Est', '2005-12-25', [1, 7, 25, 28, 31]),
 'rq07': ('RQ', B16, 'cdf', 'Responses of the Congregation for the Doctrine of the Faith to some questions regarding certain aspects of the doctrine on the Church', None, '2007-06-29', [('from', r'^Did the Second Vatican Council')]),
 'sp':   ('SUMP', B16, 'papal', 'Apostolic Letter (Motu Proprio)', 'Summorum Pontificum', '2007-07-07', [r'^It is therefore permitted to celebrate', r'^Art\. 2\b', r'^Art\. 5, §1']),
 'ss':   ('SS', B16, 'papal', 'Encyclical Letter', 'Spe Salvi', '2007-11-30', [2, 44, 45, 46, 47, 48]),
 'dp08': ('DPER', B16, 'cdf', 'Instruction of the Congregation for the Doctrine of the Faith on certain bioethical questions', 'Dignitas Personae', '2008-09-08', [4, 5, 12, 14, 15, 16, 19, 34]),
 'civ':  ('CIV', B16, 'papal', 'Encyclical Letter', 'Caritas in Veritate', '2009-06-29', [2, 6, 34, 36, 57, 67]),
 'ac':   ('ANC', B16, 'papal', 'Apostolic Constitution', 'Anglicanorum Coetibus', '2009-11-04', [r'^This single Church of Christ', r'^I\. §1', r'^VI\. §1']),
 'vd':   ('VD', B16, 'papal', 'Post-Synodal Apostolic Exhortation', 'Verbum Domini', '2010-09-30', [19]),
 'ren':  ('REN', B16, 'papal', 'Declaratio (renunciation of the office of Bishop of Rome)', None, '2013-02-10', [r'^I have convoked you']),
 'int13':('IV', F, 'interview', 'Press conference on the return flight from Rio de Janeiro', None, '2013-07-28', [r'[Ww]ho am I to judge']),
 'eg':   ('EG', F, 'papal', 'Apostolic Exhortation', 'Evangelii Gaudium', '2013-11-24', [36, 47, 104, 222, 231, 234, 247]),
 'ls':   ('LS', F, 'papal', 'Encyclical Letter', "Laudato Si'", '2015-05-24', [23, 67, 117, 120, 155]),
 'al':   ('AL', F, 'papal', 'Post-Synodal Apostolic Exhortation', 'Amoris Laetitia', '2016-03-19', [300, 301, 302, 303, 304, 305]),
 'pd':   ('PD', F, 'cdf', 'Letter of the Congregation for the Doctrine of the Faith on certain aspects of Christian salvation', 'Placuit Deo', '2018-02-22', [2, 3, 4, 10, 15]),
 'ge':   ('GE', F, 'papal', 'Apostolic Exhortation', 'Gaudete et Exsultate', '2018-03-19', [36, 47, 49, 101, 102]),
 'ccc18':('CCC', F, 'catechism', 'New text of the Catechism of the Catholic Church, approved by Francis (Rescriptum ex Audientia)', None, '2018-08-01', [2267]),
 'dp18': ('LDP', F, 'cdf', 'Letter of the Congregation for the Doctrine of the Faith to the Bishops regarding the new revision of number 2267 of the Catechism', None, '2018-08-01', [2, 3, 7, 8]),
 'bap20':('RBF', F, 'cdf', 'Responses of the Congregation for the Doctrine of the Faith on the validity of Baptism conferred with the formula "We baptize you"', None, '2020-06-24', [r'^RESPONSES TO QUESTIONS', r'^(First|Second) question', r'^To the (first|second) question', r'^The Supreme Pontiff']),
 'sb':   ('SB', F, 'cdf', 'Letter of the Congregation for the Doctrine of the Faith on the care of persons in the critical and terminal phases of life', 'Samaritanus Bonus', '2020-07-14', [r'intrinsically evil act', r'^The Church ’?s?.{0,3}teaching|^Therefore, the Church']),
 'ft':   ('FT', F, 'papal', 'Encyclical Letter', 'Fratelli Tutti', '2020-10-03', [120, 256, 258, 263, 269]),
 'sd21': ('SDOM', F, 'papal', 'Apostolic Letter (Motu Proprio)', 'Spiritus Domini', '2021-01-10', [('from', r'^Consequently, after having heard')]),
 'rsu':  ('RBU', F, 'cdf', 'Responsum of the Congregation for the Doctrine of the Faith to a dubium regarding the blessing of the unions of persons of the same sex', None, '2021-02-22', [('from', r'^TO THE QUESTION PROPOSED')]),
 'tc':   ('TC', F, 'papal', 'Apostolic Letter (Motu Proprio)', 'Traditionis Custodes', '2021-07-16', [r'^Art\. 1\b', r'^Art\. 2\b', r'^Art\. 8\b']),
 'fs':   ('FS', F, 'cdf', 'Declaration of the Dicastery for the Doctrine of the Faith on the pastoral meaning of blessings', 'Fiducia Supplicans', '2023-12-18', [4, 5, 11, 31, 32, 38, 39, 40, 41]),
 'fsp':  ('FSPR', F, 'cdf', 'Press release of the Dicastery for the Doctrine of the Faith concerning the reception of Fiducia supplicans', None, '2024-01-04', [1]),
 'gv':   ('GV', F, 'cdf', 'Note of the Dicastery for the Doctrine of the Faith on the validity of the Sacraments', 'Gestis Verbisque', '2024-02-02', [11, 12, 13, 26]),
 'dinf': ('DIN', F, 'cdf', 'Declaration of the Dicastery for the Doctrine of the Faith on human dignity', 'Dignitas Infinita', '2024-04-02', [1, 7, 8, 47, 48, 52, 55, 56, 59, 60]),
 'an':   ('ANO', F, 'cdf', 'Note of the Dicastery for the Doctrine of the Faith and the Dicastery for Culture and Education on the relationship between artificial intelligence and human intelligence', 'Antiqua et Nova', '2025-01-28', [30, 35, 104, 117]),
 'dt':   ('DT', L14, 'papal', 'Apostolic Exhortation', 'Dilexi Te', '2025-10-04', [16, 103, 110]),
 'mpf':  ('MPF', L14, 'cdf', 'Doctrinal Note of the Dicastery for the Doctrine of the Faith on some Marian titles regarding Mary\'s cooperation in the work of salvation', 'Mater Populi Fidelis', '2025-11-04', [17, 18, 22, 23, 24, 28, 29]),
 'uif':  ('UIF', L14, 'papal', 'Apostolic Letter on the 1700th anniversary of the Council of Nicaea', 'In Unitate Fidei', '2025-11-23', [2, 4, 8]),
 'uc':   ('UC', L14, 'cdf', 'Doctrinal Note of the Dicastery for the Doctrine of the Faith on the value of matrimony as an exclusive union and mutual belonging', 'Una Caro', '2025-11-25', [1, 116, 154, 155]),
 'mh':   ('MH', L14, 'papal', 'Encyclical Letter', 'Magnifica Humanitas', '2026-05-15', [48, 59, 68, 100, 112, 197]),
 'vam':  ('VAM', L14, 'cdf', 'Note of the Dicastery for the Doctrine of the Faith on the transmission of the faith in an epochal change', 'Venite ad Me', '2026-10-22', [2, 72, 73, 74]),
}
NOTE = re.compile(r'^(\[\s?\d+\s?\]|\(\d+\)|\d{1,3}\s+[A-Z]|Cf\.|Ibid|See )|^(Rome, from the Offices|Given in Rome|Given at|From the Vatican|Rome, at Saint Peter|Vatican City|Luis F\. Card|Joseph Card|William Card|Gerhard|Víctor Manuel|Card\. |✠|\+ )')
END = re.compile(r'^(Rome, from the Offices|Given in Rome|Given at Rome|From the Vatican|Rome, at Saint Peter|Done in Rome)')
def keep(t):
    return not NOTE.search(t) and not (len(t) < 260 and re.search(r'\bAAS\b|\d{4}\),? \d', t))
out = []
for k, (pre, era, weight, kind, title, date, sel) in D.items():
    P = paras(f'../vat/docs3/{k}.html'); H = list(HEADS)
    end = next((i for i, (_, t) in enumerate(P) if END.search(t)), len(P))     # the place and date close the text
    P, H = P[:end], H[:end]
    y, m, d = (int(x) for x in date.split('-'))
    groups = []
    if all(isinstance(s, int) for s in sel):
        for a in sel:
            ps = [t for (n, t) in P if n == a and keep(t)]
            if not ps: print('MISSING', k, a); continue
            h = next((head(H[i], title) for i in range(len(P) - 1, -1, -1) if P[i][0] == a and head(H[i], title)), None)
            groups.append((pre + str(a), ps, h))
    else:
        if isinstance(sel[0], tuple):
            i0 = next(i for i, (_, t) in enumerate(P) if re.search(sel[0][1], t))
            ps = [t for (_, t) in P[i0:] if keep(t)]
        else:
            ps = [t for (_, t) in P if keep(t) and any(re.search(r, t) for r in sel)]
        if not ps: print('MISSING', k, sel); continue
        groups.append((pre + (f'{y}{m:02d}{d:02d}' if pre == 'IV' else ''), ps, None))
    for eid, ps, h in groups:
        text = [clean(p) for p in ps]
        src = f'[From the {kind}, "{title}," {fmt((str(y), m, d))}]' if title else f'[From the {kind}, {fmt((str(y), m, d))}]'
        out.append({'id': eid, 'era': era, 'topic': h or title or kind, 'source': src, 'text': text, 'weight': weight, '_s': (y, m, d)})
# Amoris Laetitia 305: its note 351 belongs with the text
notes = json.load(open('../vat/other/al_notes.json'))
for e in out:
    if e['id'] == 'AL305': e['text'].append('[Note 351:] ' + clean(notes['351']))
out.sort(key=lambda e: e['_s'])
for e in out: del e['_s']
json.dump(out, open('entries3.json', 'w'), ensure_ascii=False, indent=1)
from collections import Counter
print(len(out), 'entries,', sum(len(' '.join(e['text']).split()) for e in out), 'words;', Counter(e['era'] for e in out))
print([ (e['id'], len(' '.join(e['text']).split())) for e in out if len(' '.join(e['text']).split()) > 900 or len(' '.join(e['text']).split()) < 40])
