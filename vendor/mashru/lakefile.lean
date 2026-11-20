import Lake
open Lake DSL

package mashruProofs
require nabt from "../../formal"
require a116 from "../alghanem-a116"

lean_lib Aql
lean_lib Dal
lean_lib Madlul
lean_lib Jisr
lean_lib Nizam
lean_lib SLGE
lean_lib Faahis
lean_lib tahaqquq

@[default_target]
lean_lib MashruProofs

lean_exe mashruAthar where
  root := `Qari.Athar
