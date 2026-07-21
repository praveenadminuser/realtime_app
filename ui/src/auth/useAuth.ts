import { useContext } from "react";

import { AuthContext } from "./AuthContext";

// Thin hook so components import one symbol instead of both the context and useContext.
export const useAuth = () => useContext(AuthContext);