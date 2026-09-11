import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/client.js'

export const useBusinessStore = defineStore('business', () => {
  const currentBusiness = ref(JSON.parse(localStorage.getItem('currentBusiness') || 'null'))
  const businesses = ref([])

  const hasBusinesses = computed(() => businesses.value.length > 0)

  async function createBusiness(name, description, website) {
    const { data } = await api.post('/auth/business', { name, description, website })
    currentBusiness.value = data
    businesses.value.push(data)
    localStorage.setItem('currentBusiness', JSON.stringify(data))
    return data
  }

  async function fetchMyBusinesses() {
    const { data } = await api.get('/auth/my-businesses')
    businesses.value = data
    if (data.length > 0 && !currentBusiness.value) {
      currentBusiness.value = data[0]
      localStorage.setItem('currentBusiness', JSON.stringify(data[0]))
    }
    return data
  }

  function setBusiness(business) {
    currentBusiness.value = business
    localStorage.setItem('currentBusiness', JSON.stringify(business))
  }

  function clearBusiness() {
    currentBusiness.value = null
    localStorage.removeItem('currentBusiness')
  }

  return { currentBusiness, businesses, hasBusinesses, createBusiness, fetchMyBusinesses, setBusiness, clearBusiness }
})
