import Lake
open Lake DSL

package nabt where
  version := v!"0.14.0"

@[default_target]
lean_lib Nabt

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
