export function profileCreationFailureMessage(status: number): string {
  if (status === 401 || status === 403) {
    return "Your local session has expired. Reopen Talent Advisor from the launcher and try again.";
  }
  if (status === 429) {
    return "Profile creation is temporarily busy. Wait a moment and try again.";
  }
  if (status === 502 || status === 503) {
    return "Talent Advisor cannot reach the profile service. Check your internet connection and try again.";
  }
  return "Your profile could not be created. Your text is still here so you can try again.";
}
