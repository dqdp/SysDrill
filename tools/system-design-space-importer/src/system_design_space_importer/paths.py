from pathlib import Path


class RunLayout:
    def __init__(self, out_dir, run_id):
        self.out_dir = Path(out_dir)
        self.run_id = run_id
        self.base_dir = self.out_dir / "runs" / run_id
        self.documents_dir = self.base_dir / "documents"
        self.fragments_dir = self.base_dir / "fragments"
        self.drafts_dir = self.base_dir / "drafts"
        self.reports_dir = self.base_dir / "reports"
        self.packages_dir = self.base_dir / "packages"

    @property
    def manifest_path(self):
        return self.base_dir / "manifest.json"

    def ensure_base(self):
        for path in [
            self.base_dir,
            self.documents_dir,
            self.fragments_dir,
            self.drafts_dir,
            self.reports_dir,
            self.packages_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)
