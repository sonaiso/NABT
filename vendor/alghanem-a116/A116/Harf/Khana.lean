/-!
# الخانةُ في Algebra: حاملٌ من تسعةٍ وعشرين وحالٌ من أربع (ADR ٣، قرارُ المالك 2026-10-12: «29 × 4»)

تعريفاتُ Algebra نفسِه، **لا تستورد نواةَ الغانم**: الترتيبُ ترتيبُ `src/entry.py` (الهمزةُ أوّلًا، والحالاتُ
«فتح، كسر، ضم، سكون»)، وهو غيرُ ترتيب `A116` (الهمزةُ آخرًا، «فتحة، ضمّة، كسرة، سكون»). فالتكافؤُ مع الغانم
لا يأتي من تطابق التعريف بل يُبرهَن في الجسر (`HarfBridge`).
-/

set_option autoImplicit false

namespace Harf

/-- الحواملُ بترتيب Algebra (`src/entry.py::ALPHABET`). -/
def alphabet : List Char := "ءابتثجحخدذرزسشصضطظعغفقكلمنهوي".toList

theorem alphabet_length : alphabet.length = 29 := by decide

theorem alphabet_nodup : alphabet.Nodup := by decide

abbrev Hamil := Fin 29

inductive Haal where
  | fath | kasr | damm | sukun
  deriving DecidableEq, Repr

def Haal.all : List Haal := [.fath, .kasr, .damm, .sukun]

structure Khana where
  hamil : Hamil
  haal : Haal
  deriving DecidableEq, Repr

def Khana.all : List Khana :=
  (List.finRange 29).flatMap fun h => Haal.all.map fun s => ⟨h, s⟩

theorem Khana.all_length : Khana.all.length = 116 := by decide

theorem Khana.mem_all (x : Khana) : x ∈ Khana.all := by
  rcases x with ⟨h, s⟩
  simp only [Khana.all, List.mem_flatMap, List.mem_map]
  exact ⟨h, List.mem_finRange h, s, by cases s <;> simp [Haal.all], rfl⟩

def hamilOf (ch : Char) : Hamil := ⟨alphabet.idxOf ch % 29, Nat.mod_lt _ (by decide)⟩

def charOf (h : Hamil) : Char := alphabet.getD h.val ' '

def k (ch : Char) (s : Haal) : Khana := ⟨hamilOf ch, s⟩

def hamza : Hamil := hamilOf 'ء'
def alif : Hamil := hamilOf 'ا'
def waw : Hamil := hamilOf 'و'
def ya : Hamil := hamilOf 'ي'
def lam : Hamil := hamilOf 'ل'

theorem named_carriers :
    hamza.val = 0 ∧ alif.val = 1 ∧ lam.val = 23 ∧ waw.val = 27 ∧ ya.val = 28 := by decide

/-- حرفُ المدّ وحركتُه المجانسة: الألفُ للفتح، والواوُ للضمّ، والياءُ للكسر. -/
def jins (h : Hamil) : Option Haal :=
  if h = alif then some .fath
  else if h = waw then some .damm
  else if h = ya then some .kasr
  else none

def sakin (x : Khana) : Bool := x.haal == .sukun

end Harf
