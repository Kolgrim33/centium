"""AUR package risk assessment."""
from datetime import datetime, timezone
from dataclasses import dataclass, field
from centium.aur import rpc, builder


@dataclass
class RiskFactor:
    message: str
    delta: int
    severity: str


@dataclass
class RiskReport:
    pkg: dict
    factors: list[RiskFactor] = field(default_factory=list)
    pkgbuild_warnings: list[str] = field(default_factory=list)
    score: int = 0

    def add(self, message: str, delta: int, severity: str = "info") -> None:
        self.factors.append(RiskFactor(message, delta, severity))
        self.score = max(0, min(100, self.score + delta))

    @property
    def level(self) -> str:
        if self.score <= 20:
            return "LOW"
        elif self.score <= 50:
            return "MEDIUM"
        elif self.score <= 75:
            return "HIGH"
        return "CRITICAL"

    @property
    def level_color(self) -> str:
        return {
            "LOW":      "green",
            "MEDIUM":   "yellow",
            "HIGH":     "red",
            "CRITICAL": "bold red",
        }[self.level]


def _days_since(unix_ts: int) -> int:
    dt = datetime.fromtimestamp(unix_ts, tz=timezone.utc)
    return (datetime.now(tz=timezone.utc) - dt).days


def assess(pkgname: str, scan_pkgbuild: bool = True) -> RiskReport | None:
    pkg = rpc.info(pkgname)
    if pkg is None:
        return None

    report = RiskReport(pkg=pkg)

    votes = pkg.get("NumVotes", 0)
    if votes == 0:
        report.add("No votes — completely untested by the community", 30, "warn")
    elif votes < 10:
        report.add(f"Only {votes} votes — very few users", 20, "warn")
    elif votes < 50:
        report.add(f"{votes} votes — limited user base", 10, "warn")
    elif votes < 200:
        report.add(f"{votes} votes — moderate community use", 0, "info")
    else:
        report.add(f"{votes} votes — well established", -10, "ok")

    popularity = pkg.get("Popularity", 0.0)
    if popularity < 0.001:
        report.add(f"Popularity {popularity:.4f} — rarely installed", 10, "warn")
    elif popularity < 0.1:
        report.add(f"Popularity {popularity:.4f} — niche package", 5, "info")
    elif popularity > 1.0:
        report.add(f"Popularity {popularity:.2f} — widely used", -10, "ok")
    else:
        report.add(f"Popularity {popularity:.3f} — moderate use", 0, "info")

    last_modified = pkg.get("LastModified", 0)
    if last_modified:
        days = _days_since(last_modified)
        if days > 365:
            report.add(f"Last updated {days} days ago — possibly abandoned", 20, "warn")
        elif days > 180:
            report.add(f"Last updated {days} days ago — infrequently maintained", 10, "warn")
        elif days > 60:
            report.add(f"Last updated {days} days ago — moderate activity", 3, "info")
        else:
            report.add(f"Last updated {days} days ago — actively maintained", -5, "ok")

    maintainer = pkg.get("Maintainer")
    if not maintainer:
        report.add("Package is orphaned — no active maintainer", 30, "warn")
    else:
        report.add(f"Maintained by {maintainer}", 0, "ok")

    ood = pkg.get("OutOfDate")
    if ood:
        days_ood = _days_since(ood)
        report.add(f"Flagged out of date {days_ood} days ago", 15, "warn")
    else:
        report.add("Not flagged out of date", -5, "ok")

    first = pkg.get("FirstSubmitted", 0)
    if first:
        age_days = _days_since(first)
        if age_days < 7:
            report.add(f"Package is only {age_days} days old — brand new, unvetted", 20, "warn")
        elif age_days < 30:
            report.add(f"Package submitted {age_days} days ago — relatively new", 10, "warn")
        else:
            report.add(f"Package has been in AUR for {age_days} days", 0, "ok")

    if scan_pkgbuild:
        try:
            pkgbase = pkg.get("PackageBase", pkgname)
            pkg_path = builder.clone_or_pull(pkgbase, rpc.clone_url(pkgbase))
            pkgbuild_text = builder.read_pkgbuild(pkg_path)
            warnings = builder.scan_pkgbuild(pkgbuild_text)
            report.pkgbuild_warnings = warnings
            if warnings:
                for w in warnings:
                    report.add(f"PKGBUILD: {w}", 25, "warn")
            else:
                report.add("PKGBUILD security scan passed", -5, "ok")
        except Exception as e:
            report.add(f"Could not scan PKGBUILD: {e}", 5, "info")

    return report
