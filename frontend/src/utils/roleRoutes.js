export function getDefaultRouteForRole(role) {
  if (role === "Administrator") {
    return "/admin/dashboard";
  }

  if (role === "Coach") {
    return "/coach/dashboard";
  }

  if (role === "Physiotherapist") {
    return "/physiotherapist/dashboard";
  }

  if (role === "Sports Scientist") {
    return "/sports-scientist/dashboard";
  }

  return "/dashboard";
}
