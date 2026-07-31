import persona from '../../../data/persona-ahmet-yilmaz.json'

/**
 * PANEL VERİ KAYNAĞI — ekibin kendi sentetik persona dosyasından türetilir.
 *
 * Kaynak dosya: data/synthetic_personas/ahmet_yilmaz.json (Üye 1 tarafından
 * yazıldı, repoda commit'li). Buradaki kopyası: src/data/persona-ahmet-yilmaz.json
 *
 * NEDEN BÖYLE: Bakım veren endpointleri backend'de henüz açılmadı (test edildi,
 * /api/patients/:id/* yolları 404 dönüyor). Panelin arayüzünü doğrulamak için
 * veri gerekiyor. Veriyi uydurmak yerine projenin resmi sentetik verisinden
 * türetiyoruz; böylece ekranda görünen her cümlenin kaynağı repoda gösterilebilir.
 *
 * ─────────────────────────────────────────────────────────────────────────
 * PERSONA DOSYASINDAN BİREBİR GELEN (hiçbir şey eklenmedi)
 *   hasta adı, doğum yılı, tanı, meslek, yaşadığı yer, bakım veren adı
 *   rutin başlıkları, açıklamaları ve saatleri (daily_routines)
 *   hasta soruları (sample_questions)
 *   asistan cevaplarının içeriği (core_memories, orientation_support)
 *
 * KURAL İLE TÜRETİLEN (aşağıda tanımlı, denetlenebilir)
 *   duygu etiketi  <- sample_questions[].expected_answer_type
 *   rutin durumu   <- saat şu andan önce mi sonra mı
 *
 * ÜRETİLEN (arayüz doğrulaması için, gerçek karşılığı yok)
 *   konuşmaların saatleri, giriş türü (yazılı/sesli)
 * ─────────────────────────────────────────────────────────────────────────
 *
 * Backend endpointleri açıldığında bu dosya kullanılmaz; caregiverService
 * içindeki kaynak anahtarı `backend` yapılır ve tek satır kod değişmez.
 */

export const PERSONA_SOURCE_FILE = 'data/synthetic_personas/ahmet_yilmaz.json'

/**
 * GÖRÜNTÜLEME ÇEVİRİSİ — geçici.
 *
 * Persona dosyasının içeriği İngilizce yazılmış (tanı, meslek, rutin adları,
 * anı metinleri), oysa hem arayüz hem hastanın soruları Türkçe. Bakım verene
 * İngilizce metin göstermemek için burada birebir çeviri tutuyoruz.
 *
 * Bu sözlük bir veri kaynağı değil, sadece çeviri. Persona dosyaları Türkçeye
 * çevrildiğinde (Üye 1'e iletilecek bir iş) bu blok tamamen silinir ve
 * `translate()` çağrıları kaldırılır.
 */
const DISPLAY_TR = {
  'Early Stage Alzheimer': 'Erken evre Alzheimer',
  mild: 'Hafif',
  moderate: 'Orta',
  'History Teacher': 'Tarih öğretmeni',
  'Kadıköy, Istanbul': 'Kadıköy, İstanbul',
  Daughter: 'Kızı',
  Son: 'Oğlu',
  // daily_routines[].activity
  'Morning medication': 'Sabah ilacı',
  'Tea and newspaper': 'Çay ve gazete',
  'Garden walk': 'Bahçe yürüyüşü',
  'Evening medication': 'Akşam ilacı',
  // daily_routines[].description
  'Takes morning medication after breakfast.': 'Kahvaltıdan sonra sabah ilacını alır.',
  'Likes drinking tea while reading the newspaper.': 'Gazete okurken çay içmeyi sever.',
  'Takes a short walk in the garden when the weather is suitable.':
    'Hava uygun olduğunda bahçede kısa bir yürüyüş yapar.',
  'Takes evening medication before going to bed.': 'Yatmadan önce akşam ilacını alır.',
  // core_memories[].content
  'His daughter is named Zeynep. She visits him every day and helps with his daily routine.':
    'Kızının adı Zeynep. Her gün ziyaret ediyor ve günlük rutinine yardım ediyor.',
  'His granddaughter is named Ayşe. He enjoys talking about Ayşe’s school and achievements.':
    'Torununun adı Ayşe. Ayşe’nin okulundan ve başarılarından konuşmayı sever.',
  "His granddaughter is named Ayşe. He enjoys talking about Ayşe's school and achievements.":
    'Torununun adı Ayşe. Ayşe’nin okulundan ve başarılarından konuşmayı sever.',
  'He worked as a history teacher at Ankara Atatürk High School for many years.':
    'Uzun yıllar Ankara Atatürk Lisesi’nde tarih öğretmenliği yaptı.',
  'He enjoys reading history books and drinking tea in the morning.':
    'Sabahları tarih kitabı okumayı ve çay içmeyi sever.',
}

function translate(value) {
  if (!value) return value
  return DISPLAY_TR[value] || value
}

/**
 * Soru tipinden duygu etiketine kural.
 *
 * Gerekçeler:
 *   orientation        -> hasta nerede olduğunu bilmiyor; yönelim kaybı kaygı belirtisi
 *   medication_reminder-> "ilacımı aldım mı" hatırlamama endişesi
 *   memory_recall      -> personada bu anıların emotional_tone alanı "positive"
 *   family_recall      -> bilgi sorusu, duygusal yük taşımıyor
 *
 * Etiket kümesi Python servisindeki SENTIMENT_LABELS ile aynı:
 * anxious | negative | neutral | positive
 */
const SENTIMENT_BY_QUESTION_TYPE = {
  orientation: 'anxious',
  medication_reminder: 'anxious',
  memory_recall: 'positive',
  family_recall: 'neutral',
}

/** Konuşmalara dağıtılacak saatler. Üretilmiş — gerçek konuşma saati yok. */
const GENERATED_TIMES = ['08:40', '10:15', '12:30', '15:05', '17:20']

function todayAt(time) {
  const [hour, minute] = time.split(':')
  const date = new Date()
  date.setHours(Number(hour), Number(minute), 0, 0)
  return date.toISOString()
}

function birthDateFromAge(age) {
  const year = new Date().getFullYear() - age
  return `${year}-01-01`
}

/**
 * Sorunun anahtar kelimeleriyle en iyi eşleşen core_memory'yi bulur.
 *
 * En az iki kelime eşleşmesi istiyoruz. Tek kelime eşleşmesi yanlış anı
 * getirebiliyor — örneğin "morning medication" sorusu, anahtar kelimeleri
 * arasında "morning" geçen çay/hobi anısıyla eşleşiyordu.
 */
function findMemoryFor(question) {
  const wanted = (question.expected_context_keywords || []).map((k) => k.toLowerCase())
  let best = null
  let bestScore = 0

  for (const memory of persona.core_memories || []) {
    const keywords = (memory.keywords || []).map((k) => k.toLowerCase())
    const score = keywords.filter((k) => wanted.some((w) => k.includes(w) || w.includes(k))).length
    if (score > bestScore) {
      best = memory
      bestScore = score
    }
  }
  return bestScore >= 2 ? best : null
}

/**
 * İlaç sorularının cevabı anılarda değil, personanın `medications` alanında.
 * Saatleri oradan okuyup cümleyi kuruyoruz — içerik personadan, cümle kalıbı
 * bizden.
 */
function medicationAnswer() {
  const meds = persona.medications || []
  if (meds.length === 0) return null

  const times = meds
    .map((med) => `${translate(med.name)} ${med.time}`)
    .join(', ')
  return `İlaç saatleriniz şöyle: ${times}. Endişelenmenize gerek yok, hatırlatıcılarınız açık.`
}

// ------------------------------------------------------------------- patient

export function buildPatient() {
  const meta = persona.metadata || {}
  const orientation = persona.orientation_support || {}

  return {
    patient_id: persona.patient_id,
    name: meta.full_name,
    birth_date: birthDateFromAge(meta.age),
    disease: translate(meta.diagnosis),
    disease_stage: translate(meta.disease_stage),
    former_profession: translate(meta.former_profession),
    living_status: translate(orientation.current_home),
    caregiver: {
      name: meta.primary_caregiver || orientation.emergency_contact_name,
      relation: translate(orientation.emergency_contact_relation),
    },
  }
}

// ------------------------------------------------------- routines & reminders

export function buildRoutines() {
  return (persona.daily_routines || []).map((routine, index) => ({
    routine_id: index + 1,
    patient_id: persona.patient_id,
    title: translate(routine.activity),
    description: translate(routine.description),
    frequency: 'Her gün',
    reminder_type: routine.reminder_type,
  }))
}

export function buildReminders() {
  return (persona.daily_routines || []).map((routine, index) => ({
    reminder_id: index + 1,
    routine_id: index + 1,
    reminder_time: routine.time,
    is_active: true,
  }))
}

/**
 * Bugünün rutin çizelgesi.
 *
 * Durum kural ile belirlenir: saati henüz gelmediyse "bekliyor", geçtiyse
 * "kayıt yok" — çünkü hastanın rutini tamamlayıp tamamlamadığını bilmiyoruz.
 * "Tamamlandı" demek uydurma olurdu; backend rutin kayıtlarını döndürmeye
 * başladığında gerçek durum buraya gelecek.
 */
export function buildRoutineLogs() {
  const now = new Date()

  return (persona.daily_routines || []).map((routine, index) => {
    const scheduled = new Date(todayAt(routine.time))
    return {
      log_id: 1000 + index,
      patient_id: persona.patient_id,
      routine_id: index + 1,
      log_date: scheduled.toISOString(),
      note: translate(routine.description),
      status: scheduled > now ? 'pending' : 'unknown',
    }
  })
}

// -------------------------------------------------------- interaction logs

export function buildInteractionLogs() {
  const questions = persona.sample_questions || []

  return questions.map((question, index) => {
    const memory = findMemoryFor(question)

    let response = null
    if (question.expected_answer_type === 'orientation') {
      response = persona.orientation_support?.reassurance_message
    } else if (question.expected_answer_type === 'medication_reminder') {
      response = medicationAnswer()
    } else if (memory) {
      response = translate(memory.content)
    }

    return {
      log_id: 2000 + index,
      patient_id: persona.patient_id,
      timestamp: todayAt(GENERATED_TIMES[index % GENERATED_TIMES.length]),
      input_type: index % 2 === 0 ? 'text' : 'voice',
      user_input: question.question,
      response: response || 'Bu soru için persona dosyasında eşleşen bir bağlam bulunamadı.',
      transcription: index % 2 === 0 ? null : question.question,
      sentiment: SENTIMENT_BY_QUESTION_TYPE[question.expected_answer_type] || 'neutral',
    }
  })
}

/** Panelin tek seferde ihtiyaç duyduğu bütün veri. */
export function buildPersonaDashboardData() {
  return {
    patient: buildPatient(),
    routines: buildRoutines(),
    reminders: buildReminders(),
    routineLogs: buildRoutineLogs(),
    interactionLogs: buildInteractionLogs(),
  }
}
