import { computed, nextTick, ref } from 'vue'
import { describe, expect, it } from 'vitest'
import { useClientPagination } from './useClientPagination'

describe('useClientPagination', () => {
  it('limits the visible slice and clamps navigation', async () => {
    const source = ref(Array.from({ length: 51 }, (_, index) => index + 1))
    const pagination = useClientPagination(computed(() => source.value))

    expect(pagination.paginatedItems.value).toHaveLength(25)
    pagination.goToPage(99)
    expect(pagination.page.value).toBe(3)
    expect(pagination.paginatedItems.value).toEqual([51])

    pagination.goToPage(0)
    expect(pagination.page.value).toBe(1)
    pagination.pageSize.value = 50
    await nextTick()
    expect(pagination.page.value).toBe(1)
    expect(pagination.paginatedItems.value).toHaveLength(50)
  })

  it('returns to the first page when the filtered collection changes', async () => {
    const source = ref(Array.from({ length: 30 }, (_, index) => index + 1))
    const pagination = useClientPagination(computed(() => source.value))

    pagination.goToPage(2)
    expect(pagination.page.value).toBe(2)
    source.value = source.value.slice(0, 3)
    await nextTick()

    expect(pagination.page.value).toBe(1)
    expect(pagination.paginatedItems.value).toEqual([1, 2, 3])
  })
})
