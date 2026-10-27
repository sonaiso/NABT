import Nabt.SixNounAcquisition

open Nabt Nabt.SixNounAcquisition

set_option maxRecDepth 10000
set_option maxHeartbeats 4000000

def departure : Foundation.Source := ⟨"independent-control", "1", "جَاءَ أَبُو زَيْدٍ"⟩
def object : Foundation.Source := ⟨"independent-control", "1", "رَأَيْتُ أَخَا زَيْدٍ"⟩
def prep : Foundation.Source := ⟨"independent-control", "1", "مَرَرْتُ بِفِي عَمْرٍو"⟩
def wrong : Foundation.Source := ⟨"independent-control", "1", "جَاءَ أَبِي زَيْدٍ"⟩
def unknownDhu : Foundation.Source := ⟨"independent-control", "1", "جَاءَ ذُو زَيْدٍ"⟩

example : (certify departure "reported context").isSome = true := by decide +kernel
example : (certify object "reported context").isSome = true := by decide +kernel
example : (certify prep "reported context").isSome = true := by decide +kernel
example : (certify wrong "reported context").isSome = false := by decide +kernel
example : (certify unknownDhu "reported context").isSome = false := by decide +kernel
example : (Foundation.project departure).status = .incomplete := by decide +kernel
example : (acquire ⟨"x", "1", "جَاءَ أَبُو زَيْدٍ "⟩).isSome = false := by decide +kernel
example : (acquire ⟨"x", "1", "جَاءَ أَبَُو زَيْدٍ"⟩).isSome = false := by decide +kernel

#print axioms Nabt.SixNounAcquisition.grammar_certified
#print axioms Nabt.SixNounAcquisition.certificate_all_nodes_licensed
#print axioms Nabt.SixNounAcquisition.certificate_case_sign
