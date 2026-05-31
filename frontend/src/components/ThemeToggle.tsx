import { useTheme } from "../context/ThemeContext";
import { Button } from "./ui";

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <Button variant="ghost" onClick={toggle} aria-label="Toggle theme" className="px-2">
      {theme === "dark" ? "☀" : "☾"}
    </Button>
  );
}
