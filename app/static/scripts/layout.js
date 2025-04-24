document.addEventListener("DOMContentLoaded", () => {
    const dot = document.getElementById("lan-status");
    const hostname = window.location.hostname;

    function isLanIP(ip) {
        // IPv4 private ranges
        if (ip.startsWith("10.") || ip.startsWith("192.168.")) return true;

        if (ip.startsWith("172.")) {
            const secondOctet = parseInt(ip.split(".")[1], 10);
            if (secondOctet >= 16 && secondOctet <= 31) return true;
        }

        // Loopback addresses (IPv4 and IPv6)
        if (ip === "localhost" || ip === "127.0.0.1" || ip === "::1") return false;

        // If it's a plain IPv4 address not in private range, assume public
        if (/^\d{1,3}(\.\d{1,3}){3}$/.test(ip)) return false;

        // If it's anything else (hostname, IPv6, etc), assume not LAN
        return false;
    }

    const isLanClient = isLanIP(hostname);

    dot.style.backgroundColor = isLanClient ? "limegreen" : "red";
});

function goHome() {
    window.location.href = "/";
}
