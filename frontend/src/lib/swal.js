import Swal from 'sweetalert2'

const swalIpac = Swal.mixin({
  buttonsStyling: false,
  customClass: {
    popup: 'ipac-swal-popup',
    title: 'ipac-swal-title',
    htmlContainer: 'ipac-swal-content',
    confirmButton: 'ipac-swal-confirm',
    cancelButton: 'ipac-swal-cancel',
  },
})

const formatMoney = (value) =>
  Number(value).toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export function confirmSaldoAFavor({ importe, saldo, importeAplicado, saldoFavor }) {
  return swalIpac.fire({
    icon: 'warning',
    title: 'El pago supera el saldo de la cuota',
    html: `
      <p>Se registrará el pago y el excedente quedará como saldo a favor.</p>
      <dl class="ipac-swal-details">
        <dt>Importe ingresado</dt><dd>$ ${formatMoney(importe)}</dd>
        <dt>Saldo de la cuota</dt><dd>$ ${formatMoney(saldo)}</dd>
        <dt>Importe que se aplicará</dt><dd>$ ${formatMoney(importeAplicado)}</dd>
        <dt>Saldo a favor resultante</dt><dd>$ ${formatMoney(saldoFavor)}</dd>
      </dl>
    `,
    showCancelButton: true,
    confirmButtonText: 'Confirmar pago',
    cancelButtonText: 'Cancelar',
    reverseButtons: true,
    focusCancel: true,
  })
}
