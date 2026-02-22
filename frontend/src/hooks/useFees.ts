import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { feesApi } from '@/services/api'
import { Fee, FeeType, FeeCreate, PaginatedResponse, FeeStats } from '@/types'

export function useFees(params?: {
  status?: string
  member_id?: number
  year?: number
  page?: number
  per_page?: number
}) {
  return useQuery<PaginatedResponse<Fee>>({
    queryKey: ['fees', params],
    queryFn: () => feesApi.getAll(params),
  })
}

export function useOverdueFees() {
  return useQuery<Fee[]>({
    queryKey: ['fees', 'overdue'],
    queryFn: () => feesApi.getOverdue(),
  })
}

export function useFeeTypes(activeOnly = true) {
  return useQuery<FeeType[]>({
    queryKey: ['feeTypes', { activeOnly }],
    queryFn: () => feesApi.getTypes(activeOnly),
  })
}

export function useFeeStats(year?: number) {
  return useQuery<FeeStats>({
    queryKey: ['fees', 'stats', year],
    queryFn: () => feesApi.getStats(year),
  })
}

export function useCreateFee() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: FeeCreate) => feesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fees'] })
    },
  })
}

export function useUpdateFee() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Fee> }) =>
      feesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fees'] })
    },
  })
}

export function useMarkFeePaid() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      paidDate,
      transactionId,
    }: {
      id: number
      paidDate?: string
      transactionId?: number
    }) => feesApi.markPaid(id, { paid_date: paidDate, transaction_id: transactionId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fees'] })
      queryClient.invalidateQueries({ queryKey: ['members'] })
    },
  })
}

export function useGenerateFees() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ feeTypeId, dueDate }: { feeTypeId: number; dueDate: string }) =>
      feesApi.generate(feeTypeId, dueDate),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fees'] })
    },
  })
}

export function useCreateFeeType() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: Partial<FeeType>) => feesApi.createType(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeTypes'] })
    },
  })
}
