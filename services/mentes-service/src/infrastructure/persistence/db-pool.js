import pg from 'pg'
import { datasourceConfig } from '../../../configs/datasource-config.js'

const { Pool } = pg

export const pool = new Pool({ connectionString: datasourceConfig.databaseUrl })
