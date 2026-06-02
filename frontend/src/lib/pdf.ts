import html2canvas from "html2canvas-pro";
import { jsPDF } from "jspdf";

/**
 * Export a DOM element (an assistant answer: text + citations + charts) to a paginated A4 PDF.
 * Uses html2canvas-pro (supports Tailwind v4 oklch colors) so the rendered text — including
 * Vietnamese — and the AntV chart canvases are captured exactly as shown.
 */
export async function exportAnswerToPdf(
  el: HTMLElement,
  filename = "finsight-answer.pdf",
): Promise<void> {
  const isDark = document.documentElement.classList.contains("dark");
  const canvas = await html2canvas(el, {
    scale: 2,
    backgroundColor: isDark ? "#0a0a0a" : "#ffffff",
    useCORS: true,
    logging: false,
  });

  const pdf = new jsPDF({ unit: "pt", format: "a4" });
  const pageW = pdf.internal.pageSize.getWidth();
  const pageH = pdf.internal.pageSize.getHeight();
  const margin = 28;
  const contentW = pageW - margin * 2;

  // Header band.
  pdf.setFillColor(99, 102, 241);
  pdf.rect(0, 0, pageW, 6, "F");
  pdf.setFont("helvetica", "bold");
  pdf.setFontSize(12);
  pdf.setTextColor(99, 102, 241);
  pdf.text("FinSight — Research answer", margin, 30);
  pdf.setDrawColor(230);
  pdf.line(margin, 40, pageW - margin, 40);

  const top = 52;
  const scaledH = (canvas.height * contentW) / canvas.width;
  const pageContentH = pageH - top - margin;

  if (scaledH <= pageContentH) {
    pdf.addImage(canvas.toDataURL("image/png"), "PNG", margin, top, contentW, scaledH);
  } else {
    // Slice the tall canvas across pages.
    const ratio = canvas.width / contentW;
    const sliceHpx = pageContentH * ratio;
    let srcY = 0;
    let first = true;
    while (srcY < canvas.height) {
      const h = Math.min(sliceHpx, canvas.height - srcY);
      const slice = document.createElement("canvas");
      slice.width = canvas.width;
      slice.height = h;
      slice.getContext("2d")!.drawImage(canvas, 0, srcY, canvas.width, h, 0, 0, canvas.width, h);
      if (!first) pdf.addPage();
      pdf.addImage(slice.toDataURL("image/png"), "PNG", margin, first ? top : margin, contentW, h / ratio);
      srcY += h;
      first = false;
    }
  }
  pdf.save(filename);
}
