/**
 * OrientAI marka işareti — pusula gülü.
 *
 * Emoji yerine inline SVG: emoji her işletim sisteminde farklı çiziliyor,
 * rengi kontrol edilemiyor ve punto ile ölçeklenirken hizası kayıyor.
 * Bu işaret `currentColor` kullanıyor, yani bulunduğu yerin rengini alıyor.
 *
 * Biçim kasten dört uçlu ve tek çizgi: 20 pikselde de 96 pikselde de
 * okunuyor. Pusula, ürünün adının ve işinin karşılığı — hastanın kaybettiği
 * şey yönelim, uygulamanın verdiği şey de o.
 */
function BrandMark({ size = 24, className = '' }) {
  return (
    <svg
      className={`brand-mark ${className}`.trim()}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      <circle cx="12" cy="12" r="9.5" stroke="currentColor" strokeWidth="1.4" />
      <path
        d="M12 5.5 L13.84 10.16 L18.5 12 L13.84 13.84 L12 18.5 L10.16 13.84 L5.5 12 L10.16 10.16 Z"
        fill="currentColor"
      />
    </svg>
  )
}

export default BrandMark
