import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { eventsApi } from '@/services/api'
import { Event, EventCreate, EventParticipant, PaginatedResponse } from '@/types'

export function useEvents(params?: {
  type?: string
  status?: string
  upcoming?: boolean
  page?: number
  per_page?: number
}) {
  return useQuery<PaginatedResponse<Event>>({
    queryKey: ['events', params],
    queryFn: () => eventsApi.getAll(params),
  })
}

export function useEvent(id: number) {
  return useQuery<Event>({
    queryKey: ['events', id],
    queryFn: () => eventsApi.getById(id),
    enabled: !!id,
  })
}

export function useEventStats(year?: number) {
  return useQuery({
    queryKey: ['events', 'stats', year],
    queryFn: () => eventsApi.getStats(year),
  })
}

export function useCreateEvent() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: EventCreate) => eventsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] })
    },
  })
}

export function useUpdateEvent() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<EventCreate> }) =>
      eventsApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['events'] })
      queryClient.invalidateQueries({ queryKey: ['events', variables.id] })
    },
  })
}

export function useDeleteEvent() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => eventsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] })
    },
  })
}

export function useOpenRegistration() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => eventsApi.openRegistration(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['events'] })
      queryClient.invalidateQueries({ queryKey: ['events', id] })
    },
  })
}

export function useCloseRegistration() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => eventsApi.closeRegistration(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['events'] })
      queryClient.invalidateQueries({ queryKey: ['events', id] })
    },
  })
}

// Participants
export function useEventParticipants(eventId: number, status?: string) {
  return useQuery<EventParticipant[]>({
    queryKey: ['events', eventId, 'participants', status],
    queryFn: () => eventsApi.getParticipants(eventId, status),
    enabled: !!eventId,
  })
}

export function useRegisterParticipant() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      eventId,
      memberId,
      notes,
    }: {
      eventId: number
      memberId: number
      notes?: string
    }) => eventsApi.registerParticipant(eventId, memberId, notes),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['events', variables.eventId] })
      queryClient.invalidateQueries({
        queryKey: ['events', variables.eventId, 'participants'],
      })
    },
  })
}

export function useUpdateParticipant() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      eventId,
      participantId,
      data,
    }: {
      eventId: number
      participantId: number
      data: { status?: string; notes?: string }
    }) => eventsApi.updateParticipant(eventId, participantId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['events', variables.eventId] })
      queryClient.invalidateQueries({
        queryKey: ['events', variables.eventId, 'participants'],
      })
    },
  })
}

export function useCancelParticipation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ eventId, participantId }: { eventId: number; participantId: number }) =>
      eventsApi.cancelParticipation(eventId, participantId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['events', variables.eventId] })
      queryClient.invalidateQueries({
        queryKey: ['events', variables.eventId, 'participants'],
      })
    },
  })
}
