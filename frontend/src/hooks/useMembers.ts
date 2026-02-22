import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { membersApi } from '@/services/api'
import { Member, MemberCreate, PaginatedResponse, MemberStats } from '@/types'

export function useMembers(params?: {
  status?: string
  search?: string
  page?: number
  per_page?: number
}) {
  return useQuery<PaginatedResponse<Member>>({
    queryKey: ['members', params],
    queryFn: () => membersApi.getAll(params),
  })
}

export function useMember(id: number) {
  return useQuery<Member>({
    queryKey: ['members', id],
    queryFn: () => membersApi.getById(id),
    enabled: !!id,
  })
}

export function useMemberStats() {
  return useQuery<MemberStats>({
    queryKey: ['members', 'stats'],
    queryFn: () => membersApi.getStats(),
  })
}

export function useCreateMember() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: MemberCreate) => membersApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members'] })
    },
  })
}

export function useUpdateMember() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<MemberCreate> }) =>
      membersApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['members'] })
      queryClient.invalidateQueries({ queryKey: ['members', variables.id] })
    },
  })
}

export function useDeleteMember() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => membersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['members'] })
    },
  })
}
