# app/routers/receipts.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
import io

from app.database import get_db
from app.models.receipt import Receipt
from app.schemas.receipt_schema import ReceiptRead
from app.services.receipt_service import ReceiptService
from app.core.permissions import admin_required

router = APIRouter(prefix="/receipts", tags=["Receipts"])


@router.post("/from_sale/{sale_id}", response_model=ReceiptRead, dependencies=[Depends(admin_required)])
def create_from_sale(sale_id: int, notes: str | None = None, db: Session = Depends(get_db)):
    service = ReceiptService(db)

    receipt = service.create_from_sale(sale_id, notes)

    return receipt


@router.get("/{receipt_id}", response_model=ReceiptRead, dependencies=[Depends(admin_required)])
def get_receipt(receipt_id: int, db: Session = Depends(get_db)) -> ReceiptRead:
    service = ReceiptService(db)

    return service.get(receipt_id)


# PDF endpoint: render simple HTML and convert to PDF if WeasyPrint available
@router.get("/{receipt_id}/pdf", response_class=StreamingResponse, dependencies=[Depends(admin_required)])
def get_receipt_pdf(receipt_id: int, db: Session = Depends(get_db)) -> StreamingResponse:
    service = ReceiptService(db)

    receipt = service.get(receipt_id)

    # Render HTML using a small template
    html = render_receipt_html(receipt, db)

    # Try to import weasyprint; if not available, return HTML
    try:
        from weasyprint import HTML

        pdf_bytes = HTML(string=html).write_pdf()

        return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf")

    except Exception as e:
        _e = e
        return StreamingResponse(io.BytesIO(html.encode("utf-8")), media_type="text/html")


def render_receipt_html(receipt: Receipt, db: Session) -> str:
    # Minimal HTML; can be expanded or use Jinja2
    lines: list[str] = [
        "<html><body style='font-family: Arial, sans-serif; font-size:12px;'>",
        f"<h2>Receipt #{receipt.id}</h2>",
        f"<div>Sale ID: {receipt.sale_id}</div>",
        f"<div>Date: {receipt.created_at}</div>",
        "<hr/>",
        "<table width='100%'>",
        "<thead><tr><th>Product</th><th>Qty</th><th>Unit</th><th>Subtotal</th></tr></thead><tbody>",
    ]

    for item in receipt.items:
        product = db.query(__import__("app.models.product", fromlist=["Product"]).Product).filter_by(id=item.product_id).first()
        pname = item.name or (product.name if product else f"#{item.product_id}")
        lines.append(f"<tr><td>{pname}</td><td>{item.quantity}</td><td>{item.unit_price}</td><td>{item.subtotal}</td></tr>")

    lines.append("</tbody></table><hr/>")
    lines.append(f"<div>Subtotal: {receipt.subtotal}</div>")
    lines.append(f"<div>Discount: {receipt.discount}</div>")
    lines.append(f"<div><strong>Total: {receipt.total}</strong></div>")
    lines.append(f"<div>Payments: {receipt.payment_summary}</div>")
    lines.append("</body></html>")

    return "\n".join(lines)
