import Lake
open Lake DSL

package nabt where
  version := v!"0.7.0"

@[default_target]
lean_lib Nabt

@[default_target]
lean_exe exportTable where
  root := `ExportTable
