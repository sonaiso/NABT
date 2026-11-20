import A116.Harf.Maqta

/-!
# السطر: الحدُّ بين كلمتين حرفٌ في الآلة (ADR ٤)

السطرُ كلماتٌ بينها حدّ. يُقرأ كلُّه بآلة المقاطع نفسِها، والحدُّ **خطوةٌ على الحال** (`hadd`):

* مدٌّ آخرَ الكلمة (`madd`، `farq`) يصير `maddHadd`: لا يليه ساكنٌ أوّلَ الكلمة التالية — المدُّ والمدغمُ
  «من كلمةٍ واحدة» (يَا + الشَّافِعِينَ مرفوض).
* مقطعٌ طويلٌ مغلقٌ آخرَ الكلمة (`tawil`، `tawilFarq`) لا يعبر الحدّ.
* وما سواهما لا يمسّه الحدّ.

والكلمتان سطرٌ من كلمتين (`joinB`).
-/

set_option autoImplicit false

namespace Harf

def hadd : Hal → Hal
  | .madd | .farq => .maddHadd
  | .tawil _ | .tawilFarq => .mayyit
  | a => a

def runLine (f : Hal → Khana → Hal) : Hal → List (List Khana) → Hal
  | a, [] => a
  | a, [w] => run f a w
  | a, w :: v :: rest => runLine f (hadd (run f a w)) (v :: rest)

def lineB (ws : List (List Khana)) : Bool := qabilWasl (runLine wasl .bad' ws)

def lineWaqfB (ws : List (List Khana)) : Bool := qabilWaqf (runLine waqf .bad' ws)

def joinB (l r : List Khana) : Bool := lineB [l, r]

def joinWaqfB (l r : List Khana) : Bool := lineWaqfB [l, r]

def yaa : List Khana := [k 'ي' .fath, k 'ا' .sukun]
def shshafiina : List Khana :=
  [k 'ش' .sukun, k 'ش' .fath, k 'ا' .sukun, k 'ف' .kasr, k 'ع' .kasr, k 'ي' .sukun, k 'ن' .fath]
def quli : List Khana := [k 'ق' .damm, k 'ل' .kasr]
def dallina : List Khana :=
  [k 'ض' .fath, k 'ا' .sukun, k 'ل' .sukun, k 'ل' .kasr, k 'ي' .sukun, k 'ن' .fath]
def lhamdu : List Khana := [k 'ل' .sukun, k 'ح' .fath, k 'م' .sukun, k 'د' .damm]

theorem satr_shawahid :
    waslB (yaa ++ shshafiina) = true ∧ joinB yaa shshafiina = false ∧
    joinB quli dallina = true ∧ joinB quli lhamdu = true ∧ lineB [quli, quli, lhamdu] = true := by
  decide

end Harf
