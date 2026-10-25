import Lake
open Lake DSL

package nabt where
  version := v!"0.20.0"

@[default_target]
lean_lib Nabt

@[default_target]
lean_exe exportClassicalWeak where
  root := `ExportClassicalWeak

@[default_target]
lean_exe exportClassicalHamza where
  root := `ExportClassicalHamza

@[default_target]
lean_exe exportClassicalGemination where
  root := `ExportClassicalGemination

@[default_target]
lean_exe exportClassicalBoundaryAffixes where
  root := `ExportClassicalBoundaryAffixes

@[default_target]
lean_exe exportImperativeParadigm where
  root := `ExportImperativeParadigm

@[default_target]
lean_exe exportPhonologicalModes where
  root := `ExportPhonologicalModes

@[default_target]
lean_exe exportClassicalReferenceReadings where
  root := `ExportClassicalReferenceReadings

@[default_target]
lean_exe exportProductiveForms where
  root := `ExportProductiveForms

@[default_target]
lean_exe exportTable where
  root := `ExportTable

@[default_target]
lean_exe exportDerivation where
  root := `ExportDerivation

@[default_target]
lean_exe exportNominalEvidence where
  root := `ExportNominalEvidence

@[default_target]
lean_exe exportInflectionEvidence where
  root := `ExportInflectionEvidence

@[default_target]
lean_exe exportDiscourseEvidence where
  root := `ExportDiscourseEvidence

@[default_target]
lean_exe exportPersonEvidence where
  root := `ExportPersonEvidence

@[default_target]
lean_exe exportConstructionEvidence where
  root := `ExportConstructionEvidence

@[default_target]
lean_exe unitDiscoveryProbe where
  root := `UnitDiscoveryProbe

lean_lib ProbeJson

@[default_target]
lean_exe progressiveUnitProbe where
  root := `ProgressiveUnitProbe

@[default_target]
lean_exe recursiveBridgeProbe where
  root := `RecursiveBridgeProbe

lean_exe exportRationalInquiry where
  root := `ExportRationalInquiry

lean_exe exportClassicalLanguageEvidence where
  root := `ExportClassicalLanguageEvidence

@[default_target]
lean_exe arabicInnaFragmentProbe where
  root := `ArabicInnaFragmentProbe

@[default_target]
lean_exe verifiedReading where
  root := `VerifiedReadingMain

@[default_target]
lean_exe classicalSemanticProbe where
  root := `ClassicalSemanticMain

@[default_target]
lean_exe qatrReading where
  root := `QatrReadingMain

@[default_target]
lean_exe lexicalDenotation where
  root := `LexicalDenotationMain

lean_exe exportRuleRouting where
  root := `ExportRuleRouting

lean_exe exportQualifiedInference where
  root := `ExportQualifiedInference
