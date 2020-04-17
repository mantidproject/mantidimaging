extern "C" {
__device__ void print_float_array(const float *array, const int N) {
  for (int i = 0; i < N; i++)
    printf("%.3f ", array[i]);
  printf("\n");
}
__device__ void print_neighbour_elements(const float *padded_array,
                                         const int index_offset,
                                         const int padded_img_width,
                                         const int id_x, const int id_y,
                                         const int filter_size) {
  for (int i = id_x; i < id_x + filter_size; i++)
    for (int j = id_y; j < id_y + filter_size; j++)
      printf("%.3f ", padded_array[index_offset + (i * padded_img_width) + j]);
  printf("\n");
}
__device__ float find_median_in_neighbour_array(float *neighbour_array,
                                                const int N) {
  int i, j;
  float key;

  for (i = 1; i < N; i++) {
    key = neighbour_array[i];
    j = i - 1;

    while (j >= 0 && neighbour_array[j] > key) {
      neighbour_array[j + 1] = neighbour_array[j];
      j = j - 1;
    }
    neighbour_array[j + 1] = key;
  }

  return neighbour_array[N / 2];
}
__device__ float find_neighbour_median(const float *padded_array,
                                       const int padded_img_width,
                                       const int id_x, const int id_y,
                                       const int filter_size) {
  float *neighbour_array = new float[filter_size * filter_size];
  int n_counter = 0;

  for (int i = id_x; i < id_x + filter_size; i++) {
    for (int j = id_y; j < id_y + filter_size; j++) {
      neighbour_array[n_counter] = padded_array[(i * padded_img_width) + j];
      n_counter += 1;
    }
  }

  float median = find_median_in_neighbour_array(neighbour_array,
                                                filter_size * filter_size);
  free(neighbour_array);
  return median;
}
__global__ void two_dimensional_median_filter(float *data_array,
                                              const float *padded_array,
                                              const int X, const int Y,
                                              const int filter_size) {
  unsigned int id_x = blockIdx.x * blockDim.x + threadIdx.x;
  unsigned int id_y = blockIdx.y * blockDim.y + threadIdx.y;

  if ((id_x >= X) || (id_y >= Y))
    return;

  unsigned int index = (id_x * Y) + id_y;
  unsigned int padded_img_width = Y + filter_size - 1;

  data_array[index] = find_neighbour_median(padded_array, padded_img_width,
                                            id_x, id_y, filter_size);
}
__global__ void two_dimensional_remove_light_outliers(float *data_array,
                                                      const float *padded_array,
                                                      const int X, const int Y,
                                                      const int filter_size,
                                                      const float diff) {
  unsigned int id_x = blockIdx.x * blockDim.x + threadIdx.x;
  unsigned int id_y = blockIdx.y * blockDim.y + threadIdx.y;

  if ((id_x >= X) || (id_y >= Y))
    return;

  unsigned int index = (id_x * Y) + id_y;
  unsigned int padded_img_width = Y + filter_size - 1;

  float median = find_neighbour_median(padded_array, padded_img_width, id_x,
                                       id_y, filter_size);

  if (data_array[index] - median >= diff)
    data_array[index] = median;
}
__global__ void two_dimensional_remove_dark_outliers(float *data_array,
                                                     const float *padded_array,
                                                     const int X, const int Y,
                                                     const int filter_size,
                                                     const float diff) {
  unsigned int id_x = blockIdx.x * blockDim.x + threadIdx.x;
  unsigned int id_y = blockIdx.y * blockDim.y + threadIdx.y;

  if ((id_x >= X) || (id_y >= Y))
    return;

  unsigned int index = (id_x * Y) + id_y;
  unsigned int padded_img_width = Y + filter_size - 1;

  float median = find_neighbour_median(padded_array, padded_img_width, id_x,
                                       id_y, filter_size);

  if (median - data_array[index] >= diff)
    data_array[index] = median;
}
}
