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

const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (character) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;',
}[character]))

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

export function confirmSensitiveUserChange({ title, userName, description, beforeRole, afterRole }) {
  const roleDetails = beforeRole || afterRole
    ? `<dl class="ipac-swal-details">
        <div><dt>Usuario</dt><dd>${escapeHtml(userName)}</dd></div>
        ${beforeRole ? `<div><dt>Rol actual</dt><dd>${escapeHtml(beforeRole)}</dd></div>` : ''}
        ${afterRole ? `<div><dt>Nuevo rol</dt><dd>${escapeHtml(afterRole)}</dd></div>` : ''}
      </dl>`
    : `<p class="ipac-swal-user">Usuario: <strong>${escapeHtml(userName)}</strong></p>`

  return swalIpac.fire({
    icon: 'warning',
    title,
    html: `<p>${escapeHtml(description)}</p>${roleDetails}`,
    showCancelButton: true,
    confirmButtonText: 'Confirmar cambio',
    cancelButtonText: 'Cancelar',
    reverseButtons: true,
    focusCancel: true,
  })
}

export function confirmFinalizarMatricula({ alumno, carrera, fechaInicio }) {
  return swalIpac.fire({
    icon: 'warning',
    title: 'Finalizar matrícula',
    html: `
      <p>La matrícula dejará de estar activa y conservará su historial.</p>
      <dl class="ipac-swal-details">
        <div><dt>Alumno</dt><dd>${escapeHtml(alumno)}</dd></div>
        <div><dt>Carrera/curso</dt><dd>${escapeHtml(carrera)}</dd></div>
        <div><dt>Fecha de inicio</dt><dd>${escapeHtml(fechaInicio)}</dd></div>
      </dl>
    `,
    showCancelButton: true,
    confirmButtonText: 'Finalizar matrícula',
    cancelButtonText: 'Cancelar',
    reverseButtons: true,
    focusCancel: true,
  })
}

export function confirmCierreCaja({ sucursal, fecha, totalEsperado, totalContado, diferencia }) {
  const hasDifference = Math.abs(Number(diferencia || 0)) > 0.005
  const differenceClass = hasDifference ? 'ipac-swal-difference-warning' : ''
  const differenceMessage = hasDifference
    ? '<p class="ipac-swal-warning-copy">La diferencia quedará registrada en el cierre.</p>'
    : '<p>Los totales coinciden.</p>'

  return swalIpac.fire({
    icon: hasDifference ? 'warning' : 'question',
    title: 'Confirmar cierre de caja',
    html: `
      <p>La caja quedará cerrada y no aceptará nuevas cobranzas ni movimientos.</p>
      <dl class="ipac-swal-details">
        <div><dt>Sucursal</dt><dd>${escapeHtml(sucursal)}</dd></div>
        <div><dt>Fecha</dt><dd>${escapeHtml(fecha)}</dd></div>
        <div><dt>Total esperado</dt><dd>$ ${formatMoney(totalEsperado)}</dd></div>
        <div><dt>Total contado</dt><dd>$ ${formatMoney(totalContado)}</dd></div>
        <div class="${differenceClass}"><dt>Diferencia</dt><dd>$ ${formatMoney(diferencia)}</dd></div>
      </dl>
      ${differenceMessage}
    `,
    showCancelButton: true,
    confirmButtonText: 'Cerrar caja',
    cancelButtonText: 'Cancelar',
    reverseButtons: true,
    focusCancel: true,
  })
}

export function confirmGeneracionCuotasMasivas({
  cantidad,
  sucursal,
  carrera,
  concepto,
  periodo,
  importe,
  totalEstimado,
}) {
  return swalIpac.fire({
    icon: 'warning',
    title: `Generar ${cantidad} cuotas`,
    html: `
      <p>La operación afectará múltiples estados de cuenta.</p>
      <dl class="ipac-swal-details">
        <div><dt>Sucursal</dt><dd>${escapeHtml(sucursal)}</dd></div>
        <div><dt>Carrera/curso</dt><dd>${escapeHtml(carrera || 'Todas')}</dd></div>
        <div><dt>Concepto</dt><dd>${escapeHtml(concepto)}</dd></div>
        <div><dt>Período</dt><dd>${escapeHtml(periodo)}</dd></div>
        <div><dt>Cantidad de alumnos</dt><dd>${cantidad}</dd></div>
        <div><dt>Importe unitario</dt><dd>$ ${formatMoney(importe)}</dd></div>
        <div><dt>Total estimado</dt><dd>$ ${formatMoney(totalEstimado)}</dd></div>
      </dl>
    `,
    showCancelButton: true,
    confirmButtonText: 'Generar cuotas',
    cancelButtonText: 'Cancelar',
    reverseButtons: true,
    focusCancel: true,
  })
}

export function showResultadoCuotasMasivas({ creadas, omitidas, errores, detalle = '' }) {
  return swalIpac.fire({
    icon: errores ? 'error' : 'info',
    title: 'Resultado de generación',
    html: `
      ${detalle ? `<p>${escapeHtml(detalle)}</p>` : ''}
      <dl class="ipac-swal-details">
        <div><dt>Creadas</dt><dd>${creadas}</dd></div>
        <div><dt>Omitidas</dt><dd>${omitidas}</dd></div>
        <div><dt>Errores</dt><dd>${errores}</dd></div>
      </dl>
    `,
    confirmButtonText: 'Continuar',
  })
}
