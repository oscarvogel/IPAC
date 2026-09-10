import { computed, ref, readonly, watch } from 'vue'

const DEFAULT_PAGE_SIZES = Object.freeze([25, 50, 100])

export function useClientPagination(items, options = {}) {
  const page = ref(1)
  const pageSize = ref(options.initialPageSize || DEFAULT_PAGE_SIZES[0])
  const pageSizes = options.pageSizes || DEFAULT_PAGE_SIZES

  const totalPages = computed(() => Math.max(1, Math.ceil(items.value.length / pageSize.value)))
  const paginatedItems = computed(() => {
    const start = (page.value - 1) * pageSize.value
    return items.value.slice(start, start + pageSize.value)
  })

  function resetPage() {
    page.value = 1
  }

  function goToPage(targetPage) {
    page.value = Math.min(Math.max(1, targetPage), totalPages.value)
  }

  watch(items, resetPage)
  watch(pageSize, resetPage)
  watch(totalPages, (nextTotalPages) => {
    if (page.value > nextTotalPages) page.value = nextTotalPages
  })

  return {
    page: readonly(page),
    pageSize,
    pageSizes,
    totalPages,
    paginatedItems,
    goToPage,
  }
}
