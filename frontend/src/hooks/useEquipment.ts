import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { equipmentApi } from '@/services/api'
import { Equipment, EquipmentCreate, Reservation, ReservationCreate } from '@/types'

export function useEquipment(params?: {
  type?: string
  status?: string
  available?: boolean
}) {
  return useQuery<Equipment[]>({
    queryKey: ['equipment', params],
    queryFn: () => equipmentApi.getAll(params),
  })
}

export function useEquipmentItem(id: number) {
  return useQuery<Equipment>({
    queryKey: ['equipment', id],
    queryFn: () => equipmentApi.getById(id),
    enabled: !!id,
  })
}

export function useEquipmentStats() {
  return useQuery({
    queryKey: ['equipment', 'stats'],
    queryFn: () => equipmentApi.getStats(),
  })
}

export function useMaintenanceDue() {
  return useQuery<Equipment[]>({
    queryKey: ['equipment', 'maintenance-due'],
    queryFn: () => equipmentApi.getMaintenanceDue(),
  })
}

export function useCreateEquipment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: EquipmentCreate) => equipmentApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipment'] })
    },
  })
}

export function useUpdateEquipment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<EquipmentCreate> }) =>
      equipmentApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['equipment'] })
      queryClient.invalidateQueries({ queryKey: ['equipment', variables.id] })
    },
  })
}

export function useDeleteEquipment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => equipmentApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipment'] })
    },
  })
}

// Reservations
export function useReservations(params?: {
  equipment_id?: number
  member_id?: number
  status?: string
  start_date?: string
  end_date?: string
}) {
  return useQuery<Reservation[]>({
    queryKey: ['reservations', params],
    queryFn: () => equipmentApi.getAllReservations(params),
  })
}

export function useEquipmentReservations(equipmentId: number, startFrom?: string) {
  return useQuery<Reservation[]>({
    queryKey: ['equipment', equipmentId, 'reservations', startFrom],
    queryFn: () => equipmentApi.getReservations(equipmentId, startFrom),
    enabled: !!equipmentId,
  })
}

export function useCreateReservation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ReservationCreate) => equipmentApi.createReservation(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reservations'] })
      queryClient.invalidateQueries({ queryKey: ['equipment'] })
    },
  })
}

export function useUpdateReservation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<ReservationCreate> }) =>
      equipmentApi.updateReservation(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reservations'] })
    },
  })
}

export function useConfirmReservation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => equipmentApi.confirmReservation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reservations'] })
    },
  })
}

export function useCancelReservation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => equipmentApi.cancelReservation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reservations'] })
    },
  })
}

export function useCompleteReservation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => equipmentApi.completeReservation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reservations'] })
    },
  })
}
