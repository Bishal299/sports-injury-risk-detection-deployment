import React, {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";


const ThemeContext = createContext();


export function ThemeProvider({ children }) {

  const [theme, setTheme] = useState(() => {

    return (
      localStorage.getItem("theme") ||
      "light"
    );

  });


  useEffect(() => {
    document.documentElement.classList.add(
      "theme-transitioning"
    );

    document.documentElement.setAttribute(
      "data-theme",
      theme
    );

    localStorage.setItem(
      "theme",
      theme
    );

    const transitionTimer = window.setTimeout(() => {
      document.documentElement.classList.remove(
        "theme-transitioning"
      );
    }, 360);

    return () => {
      window.clearTimeout(transitionTimer);
      document.documentElement.classList.remove(
        "theme-transitioning"
      );
    };

  }, [theme]);


  const toggleTheme = () => {

    setTheme((currentTheme) =>
      currentTheme === "light"
        ? "dark"
        : "light"
    );

  };


  return (
    <ThemeContext.Provider
      value={{
        theme,
        toggleTheme,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}


export function useTheme() {

  return useContext(
    ThemeContext
  );

}
