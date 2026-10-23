import Lake
open Lake DSL

package nabt where
  version := v!"0.10.0"

@[default_target]
lean_lib Nabt

@[default_target]
lean_exe exportTable where
  root := `ExportTable

@[default_target]
lean_exe exportDerivation where
  root := `ExportDerivation
