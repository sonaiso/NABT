# معجمُ لين — المصدرُ والرخصة

نصُّ `README.md` في `alpheios-project/lan` عند الإيداع `7dd04e1182c13a4b0883978867d2a3b04616542a`
(2026-04-19) حرفيًّا:

> An Arabic-English Lexicon. London. Williams and Norgate. 1863.
>
> Original Digitization provided by the Perseus Digital Library at Tufts University, under the support of the U.S. Department of Education and the Max Planck Society.
>
> Corrections to digitization added by the Alpheios Project, Ltd.
>
> This work is licensed under a Creative Commons Attribution-ShareAlike 3.0 United States License.  http://creativecommons.org/licenses/by-sa/3.0/us/

- الملفّاتُ في `tei/` هي `db/lexica/ara/lan/u*.xml` من ذلك الإيداع بأعيانها، مضغوطةً بـ`gzip -n -9`؛ وبصمةُ كلٍّ
  منها بعد فكّ الضغط في `tools/gen_lane.py` (`LANE_SOURCES`).
- `lane-lines.txt.gz` و`lane-masdar.tsv` و`lane-plural.tsv` مشتقّةٌ منها بتلك الأداة، فهي تحت الرخصة نفسِها
  (CC BY-SA 3.0 US، النسبةُ إلى Perseus وAlpheios أعلاه).
