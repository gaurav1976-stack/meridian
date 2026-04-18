/**
 * Meridian Airport PMO suite
 * (c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
 * Proprietary — unauthorised copying, distribution, modification or use prohibited.
 */
export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="border-t border-meridian-100 bg-white px-6 py-3 text-xs text-meridian-600">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span>
          &copy; {year} <strong className="text-meridian-800">GV Softwares</strong>. Developed by{" "}
          <strong className="text-meridian-800">Gaurav Vatsa</strong>. All rights reserved.
        </span>
        <span className="text-meridian-500">
          Meridian Airport PMO suite — proprietary software
        </span>
      </div>
    </footer>
  );
}
