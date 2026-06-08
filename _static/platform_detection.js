/**
 * Detects the user's OS and adds a CSS class to <body>, enabling
 * OS-specific inline code snippet display via custom.css
 */

const OS_CLASS_MAP = [
    { match: (platform) => platform.includes("MAC"), cssClass: "os-mac" },
    { match: (platform) => platform.includes("WIN"), cssClass: "os-windows" },
    { match: (platform) => platform.includes("LINUX"), cssClass: "os-linux" },
];
const DEFAULT_OS_CLASS = "os-linux";

function detectOsClass() {
    const platform = (navigator.userAgentData?.platform ?? navigator.platform ?? "").toUpperCase();
    return OS_CLASS_MAP.find(({ match }) => match(platform))?.cssClass ?? DEFAULT_OS_CLASS;
}

document.addEventListener("DOMContentLoaded", () => {
    document.body.classList.add(detectOsClass());
});
